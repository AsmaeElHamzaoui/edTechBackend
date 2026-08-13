import chromadb
from sentence_transformers import SentenceTransformer


# Modèle d'embeddings
model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ChromaDB local
client = chromadb.PersistentClient(
    path="./chroma_db"
)


# Collection qui contient les chunks
collection = client.get_or_create_collection(
    name="document_chunks"
)


def generate_embeddings_for_document(document):

    chunks = document.chunks.all().order_by("chunk_index")

    if not chunks.exists():
        return 0

    ids = []
    texts = []
    metadatas = []

    for chunk in chunks:

        ids.append(
            f"document_{document.id}_chunk_{chunk.chunk_index}"
        )

        texts.append(
            chunk.content
        )

        metadatas.append({
            "document_id": document.id,
            "document_title": document.title,
            "chunk_index": chunk.chunk_index,
            "page": chunk.page or 0
        })

    # Génération des embeddings
    embeddings = model.encode(
        texts,
        show_progress_bar=True
    )

    # Enregistrement dans ChromaDB
    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=metadatas
    )

    return len(chunks)


def delete_document_embeddings(document_id):
    """
    Supprime les chunks d'un document dans ChromaDB.
    """
    collection.delete(
        where={"document_id": document_id}
    )