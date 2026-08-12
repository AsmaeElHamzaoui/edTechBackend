import json
from django.http import StreamingHttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, AskQuestionSerializer
from chat.services.chat_service import ask_question
from chat.services.memory_service import build_conversation_history, add_message
from documents.services.rag_service import build_rag_context
from documents.services.llm_service import generate_answer_stream, generate_follow_up_actions
from documents.models import Document


class ConversationViewSet(viewsets.ModelViewSet):

    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        messages = conversation.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @messages.mapping.post
    def add_message(self, request, pk=None):
        conversation = self.get_object()

        if conversation.user != request.user:
            return Response({"detail": "Non autorisé."}, status=status.HTTP_403_FORBIDDEN)

        if conversation.document and conversation.document.uploaded_by != request.user:
            return Response({"detail": "Document non autorisé."}, status=status.HTTP_403_FORBIDDEN)

        serializer = AskQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]

        result = ask_question(conversation, question)
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="stream")
    def stream(self, request, pk=None):
        """
        Endpoint SSE : POST /api/chat/conversations/{id}/stream/
        Body: { "question": "...", "document_id": <optional> }

        Retourne la réponse IA progressivement via Server-Sent Events.
        Le frontend écoute avec EventSource ou fetch + ReadableStream.
        """
        conversation = self.get_object()

        if conversation.user != request.user:
            return Response({"detail": "Non autorisé."}, status=status.HTTP_403_FORBIDDEN)

        # Validation document si la conversation y est liée
        document = conversation.document
        if document:
            if document.uploaded_by != request.user:
                return Response({"detail": "Document non autorisé."}, status=status.HTTP_403_FORBIDDEN)
            if document.status != Document.Status.READY:
                return Response(
                    {"detail": "Le document n'est pas encore prêt (statut: %s)." % document.status},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = AskQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]
        complexity = serializer.validated_data.get("complexity", "normal")

        # 1. Historique de mémoire
        history = build_conversation_history(conversation, limit=10)

        # 2. Sauvegarde de la question utilisateur
        add_message(conversation, "user", question)

        # 3. RAG context
        document_id = document.id if document else None
        rag_result = build_rag_context(question, n_results=3, document_id=document_id)
        context = rag_result["context"]
        sources = rag_result["sources"]

        # 4. SSE generator
        def event_stream():
            full_answer = ""

            # Envoyer les sources en premier événement
            yield f"event: sources\ndata: {json.dumps(sources, ensure_ascii=False)}\n\n"

            # Streamer les tokens de la réponse
            for chunk in generate_answer_stream(question, context, history, complexity=complexity):
                full_answer += chunk
                # Format SSE standard : "data: ...\n\n"
                payload = json.dumps({"token": chunk}, ensure_ascii=False)
                yield f"data: {payload}\n\n"

            # Générer et envoyer les actions de suivi
            actions = generate_follow_up_actions(question, full_answer)
            yield f"event: follow_up\ndata: {json.dumps(actions, ensure_ascii=False)}\n\n"

            # Événement final indiquant la fin du stream
            yield f"event: done\ndata: {json.dumps({'answer': full_answer}, ensure_ascii=False)}\n\n"

            # Sauvegarder la réponse complète en BDD
            add_message(conversation, "assistant", full_answer)

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream"
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
