from documents.models import Document, DocumentChunk


def split_text_with_pages(pages, chunk_size=1000, overlap=200):
    """
    Découpe le texte en chunks en conservant le numéro de page.
    pages = [(page_num, text), ...]
    Retourne [(chunk_text, page_num), ...]
    """
    chunks = []

    for page_num, page_text in pages:
        start = 0
        text_length = len(page_text)

        while start < text_length:
            end = start + chunk_size
            chunk = page_text[start:end].strip()

            if chunk:
                chunks.append((chunk, page_num))

            start += chunk_size - overlap

    return chunks


def create_document_chunks(document: Document, pages=None):
    """
    Crée les chunks en base de données.
    Si pages est fourni (liste de tuples page_num, text), utilise le découpage par page.
    Sinon, découpe le texte extrait sans info de page (rétrocompatibilité).
    """
    # Supprimer les anciens chunks
    document.chunks.all().delete()

    document_chunks = []

    if pages:
        chunks_with_pages = split_text_with_pages(pages)
        for index, (content, page_num) in enumerate(chunks_with_pages):
            document_chunks.append(
                DocumentChunk(
                    document=document,
                    content=content,
                    chunk_index=index,
                    page=page_num,
                )
            )
    else:
        # Fallback : découpage simple sans page
        from documents.services.text_chunker import split_text
        chunks = split_text(document.extracted_text)
        for index, content in enumerate(chunks):
            document_chunks.append(
                DocumentChunk(
                    document=document,
                    content=content,
                    chunk_index=index,
                )
            )

    DocumentChunk.objects.bulk_create(document_chunks)
    return document_chunks