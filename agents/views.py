from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from documents.models import Document
from .orchestrator_agent import OrchestratorAgent


class OrchestratorView(APIView):
    """
    Point d'entrée unique de l'architecture Multi-Agent.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get("prompt")
        document_id = request.data.get("document_id")

        if not text or not document_id:
            return Response(
                {"detail": "Les champs 'prompt' et 'document_id' sont obligatoires."},
                status=status.HTTP_400_BAD_REQUEST
            )

        document = get_object_or_404(Document, id=document_id, uploaded_by=request.user)
        
        if document.status != Document.Status.READY:
            return Response(
                {"detail": "Le document n'est pas prêt."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # L'orchestrateur prend le relais
            result = OrchestratorAgent.process(request.user, document, text)
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
