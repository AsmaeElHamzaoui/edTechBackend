from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from .models import Document
from .serializers import DocumentSerializer

from .services.pdf_extractor import extract_text_from_pdf
from .services.chunk_service import create_document_chunks
from .services.embedding_service import generate_embeddings_for_document, delete_document_embeddings
from .services.quota_service import QuotaService
from django.conf import settings
import boto3


class DocumentListCreateView(generics.ListCreateAPIView):

    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(
            uploaded_by=self.request.user
        ).order_by("-uploaded_at")

    def perform_create(self, serializer):
        user = self.request.user
        file = self.request.data.get("file")
        
        if not file:
            raise ValidationError({"file": "Un fichier est requis."})

        # 0. Vérification doublon (même utilisateur + même nom de fichier)
        if Document.objects.filter(uploaded_by=user, file__endswith=file.name).exists():
            raise ValidationError(
                {"detail": f"Vous avez déjà uploadé un document nommé « {file.name} »."}
            )

        # 1. Vérification du quota
        can_upload, message = QuotaService.can_upload(user, file.size)
        if not can_upload:
            raise ValidationError({"detail": message})

        # 2. Réservation du quota
        QuotaService.reserve_storage(user, file.size)

        # 3. Création du document (UPLOADED)
        document = serializer.save(
            uploaded_by=user,
            status=Document.Status.UPLOADED
        )
        
        # 4. Déclenchement de la tâche asynchrone Celery
        from documents.tasks import process_document_task
        process_document_task.delay(document.id)


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(
            uploaded_by=self.request.user
        )

    def perform_destroy(self, instance):
        # 1. Nettoyer ChromaDB
        delete_document_embeddings(instance.id)
        
        # 2. Libérer le quota
        file_size = instance.file.size if instance.file else 0
        QuotaService.release_storage(instance.uploaded_by, file_size)
        
        # 3. Supprimer le fichier physique
        if instance.file:
            instance.file.delete(save=False)
            
        # 4. Supprimer le document (cascade pour les chunks DB)
        instance.delete()


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.summary_service import generate_document_summary


class DocumentSummaryView(APIView):
    """
    Endpoint pour générer un résumé ou une fiche de synthèse d'un document.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            document = Document.objects.get(id=pk, uploaded_by=request.user)
        except Document.DoesNotExist:
            return Response(
                {"detail": "Document introuvable ou accès interdit."},
                status=status.HTTP_404_NOT_FOUND
            )

        if document.status != Document.Status.READY:
            return Response(
                {"detail": "Le document doit avoir le statut READY pour être résumé."},
                status=status.HTTP_400_BAD_REQUEST
            )

        summary_type = request.data.get("type", "summary")
        
        if summary_type not in ["summary", "study_sheet"]:
            return Response(
                {"detail": "Le paramètre 'type' doit être 'summary' ou 'study_sheet'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            summary_text = generate_document_summary(document, summary_type)
            return Response({
                "document_id": document.id,
                "type": summary_type,
                "content": summary_text
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors de la génération: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PresignedUrlView(APIView):
    """
    GET /api/documents/presigned-url/?filename=document.pdf&content_type=application/pdf
    Génère une URL présignée pour un upload direct vers S3 (si USE_S3 est activé).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not getattr(settings, 'USE_S3', False):
            return Response({"detail": "Le stockage S3 n'est pas activé sur ce serveur."}, status=status.HTTP_400_BAD_REQUEST)

        filename = request.query_params.get("filename")
        content_type = request.query_params.get("content_type", "application/pdf")

        if not filename:
            return Response({"detail": "Le paramètre filename est requis."}, status=status.HTTP_400_BAD_REQUEST)

        # Générer un nom de fichier unique
        import uuid
        import os
        ext = os.path.splitext(filename)[1]
        unique_filename = f"documents/{uuid.uuid4()}{ext}"

        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        )

        try:
            response = s3_client.generate_presigned_post(
                settings.AWS_STORAGE_BUCKET_NAME,
                unique_filename,
                Fields={"Content-Type": content_type},
                Conditions=[{"Content-Type": content_type}, ["content-length-range", 1, 50 * 1024 * 1024]], # Max 50MB
                ExpiresIn=3600
            )
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)