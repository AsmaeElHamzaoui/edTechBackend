from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Document
from .serializers import DocumentSerializer

from .services.pdf_extractor import extract_text_from_pdf
from .services.chunk_service import create_document_chunks


class DocumentListCreateView(generics.ListCreateAPIView):

    serializer_class = DocumentSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        return Document.objects.filter(
            uploaded_by=self.request.user
        ).order_by("-uploaded_at")

    def perform_create(self, serializer):

        # 1. Création du document
        document = serializer.save(
            uploaded_by=self.request.user
        )

        # 2. Extraction du texte
        extracted_text = extract_text_from_pdf(
            document.file.path
        )

        # 3. Sauvegarde du texte
        document.extracted_text = extracted_text

        document.save(
            update_fields=["extracted_text"]
        )

        # 4. Création des chunks
        create_document_chunks(document)


class DocumentDetailView(generics.RetrieveDestroyAPIView):

    serializer_class = DocumentSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        return Document.objects.filter(
            uploaded_by=self.request.user
        )