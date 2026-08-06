from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from documents.models import Document
from documents.services.rag_service import build_rag_context
from documents.services.llm_service import generate_answer

from .models import Conversation, Message
from .serializers import AskQuestionSerializer


class AskQuestionView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        # =====================================================
        # 1. VALIDATION DES DONNÉES
        # =====================================================

        serializer = AskQuestionSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"]
        document_id = serializer.validated_data["document_id"]
        conversation_id = serializer.validated_data.get(
            "conversation_id"
        )

        # =====================================================
        # 2. RÉCUPÉRER LE DOCUMENT
        # =====================================================

        try:
            document = Document.objects.get(
                id=document_id,
                uploaded_by=request.user
            )

        except Document.DoesNotExist:

            return Response(
                {
                    "detail": "Document introuvable ou accès interdit."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # =====================================================
        # 3. RÉCUPÉRER OU CRÉER LA CONVERSATION
        # =====================================================

        if conversation_id:

            try:
                conversation = Conversation.objects.get(
                    id=conversation_id,
                    user=request.user
                )

            except Conversation.DoesNotExist:

                return Response(
                    {
                        "detail": "Conversation introuvable."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        else:

            conversation = Conversation.objects.create(
                user=request.user,
                document=document,
                title=question[:255]
            )

        # =====================================================
        # 4. SAUVEGARDER LA QUESTION
        # =====================================================

        Message.objects.create(
            conversation=conversation,
            role="USER",
            content=question
        )

        # =====================================================
        # 5. RECHERCHE RAG
        # =====================================================

        rag_result = build_rag_context(
            question,
            n_results=3,
            document_id=document.id
        )

        # =====================================================
        # 6. GÉNÉRATION GEMINI
        # =====================================================

        answer = generate_answer(
            question,
            rag_result["context"]
        )

        # =====================================================
        # 7. SAUVEGARDER LA RÉPONSE
        # =====================================================

        Message.objects.create(
            conversation=conversation,
            role="ASSISTANT",
            content=answer
        )

        # =====================================================
        # 8. RÉPONSE API
        # =====================================================

        return Response(
            {
                "conversation_id": conversation.id,
                "question": question,
                "answer": answer,
                "sources": rag_result["sources"]
            },
            status=status.HTTP_200_OK
        )

