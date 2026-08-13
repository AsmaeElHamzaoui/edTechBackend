from documents.services.retrieval_service import search_similar_chunks


def build_rag_context(question, n_results=3, document_id=None):

    results = search_similar_chunks(
        question=question,
        n_results=n_results,
        document_id=document_id
    )

    if not results:
        return {
            "context": "",
            "sources": []
        }

    context_parts = []
    sources = []

    for index, result in enumerate(results, start=1):

        context_parts.append(
            f"[SOURCE {index}]\n"
            f"Document: {result['document_title']}\n"
            f"Page: {result.get('page', '?')}\n"
            f"Chunk: {result['chunk_index']}\n"
            f"Content:\n{result['content']}"
        )

        sources.append({
            "source": index,
            "document_id": result["document_id"],
            "document_title": result["document_title"],
            "chunk_index": result["chunk_index"],
            "page": result.get("page"),
            "distance": result["distance"]
        })

    context = "\n\n".join(context_parts)

    return {
        "context": context,
        "sources": sources
    }