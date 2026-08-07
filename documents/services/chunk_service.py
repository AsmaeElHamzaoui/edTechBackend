from documents.models import Document, DocumentChunk
from documents.services.text_chunker import split_text


def create_document_chunks(document: Document):

    # Supprimer les anciens chunks
    document.chunks.all().delete()

    # Découper le texte
    chunks = split_text(
        document.extracted_text
    )

    # Créer les chunks
    document_chunks = []

    for index, content in enumerate(chunks):

        document_chunks.append(
            DocumentChunk(
                document=document,
                content=content,
                chunk_index=index
            )
        )

    # Enregistrer tous les chunks en une seule opération
    DocumentChunk.objects.bulk_create(
        document_chunks
    )

    return document_chunks