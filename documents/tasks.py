import logging
from celery import shared_task
from documents.models import Document
from documents.services.pdf_extractor import extract_text_from_pdf
from documents.services.chunk_service import create_document_chunks
from documents.services.embedding_service import generate_embeddings_for_document

logger = logging.getLogger(__name__)


@shared_task
def process_document_task(document_id):
    try:
        document = Document.objects.get(id=document_id)
        if document.status != Document.Status.UPLOADED:
            return

        # Update status to processing
        document.status = Document.Status.PROCESSING
        document.save(update_fields=['status'])

        # 1. Extraction page par page (with OCR fallback)
        pages = extract_text_from_pdf(document.file.path)
        full_text = "\n".join(text for _, text in pages)
        document.extracted_text = full_text
        document.save(update_fields=['extracted_text'])

        # 2. Chunking (page-aware)
        create_document_chunks(document, pages=pages)

        # 3. Embedding
        generate_embeddings_for_document(document)

        # 4. Ready
        document.status = Document.Status.READY
        document.save(update_fields=['status'])

        # 5. Notifier l'utilisateur
        from agents.notification_agent import NotificationAgent
        NotificationAgent.notify_document_ready(document)

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        try:
            document = Document.objects.get(id=document_id)
            document.status = Document.Status.FAILED
            document.error_message = str(e)
            document.save(update_fields=['status', 'error_message'])

            # Notifier l'utilisateur de l'échec
            from agents.notification_agent import NotificationAgent
            NotificationAgent.notify_document_failed(document)
        except Exception as update_err:
            logger.error(f"Failed to update document status to FAILED: {update_err}")
