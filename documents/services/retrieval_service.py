from documents.services.embedding_service import collection


def search_similar_chunks(question, n_results=3, document_id=None):

    # Filtres ChromaDB
    where = None

    if document_id is not None:
        where = {
            "document_id": document_id
        }

    results = collection.query(
        query_texts=[question],
        n_results=n_results,
        where=where
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    retrieved_chunks = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):
        retrieved_chunks.append({
            "content": document,
            "document_id": metadata.get("document_id"),
            "document_title": metadata.get("document_title"),
            "chunk_index": metadata.get("chunk_index"),
            "page": metadata.get("page"),
            "distance": distance,
        })

    return retrieved_chunks