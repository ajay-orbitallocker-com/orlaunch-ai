from rag.ingestion.ingest_all import prepare_all_chunks
from rag.embeddings.batch import run_batch_embedding
from config import client, EMBEDDING_MODEL, chromadb, chroma_client, CHROMA_PATH, collection, COLLECTION_NAME


def build_metadata(chunk: dict) -> dict:
    """Extract metadata fields from a standardized chunk dict."""
    metadata = {
        "chunk_id": str(chunk.get("chunk_id", "")),
        "id": str(chunk.get("id", chunk.get("source_id", ""))),
        "title": str(chunk.get("title", "")),
        "category": str(chunk.get("category", "General")),
        "source": str(chunk.get("source", "Unknown")),
        "url": str(chunk.get("url", ""))
    }
    if chunk.get("trl_current") is not None:
        metadata["trl_current"] = int(chunk["trl_current"])
    return metadata


def store_chunks(embedded_chunks: list[dict]) -> None:
    """
    Write embedded chunks into ChromaDB with unified metadata across all categories.
    """
    if not embedded_chunks:
        print("No chunks to store.")
        return

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for chunk in embedded_chunks:
        metadata = build_metadata(chunk)
        ids.append(chunk["chunk_id"])
        embeddings.append(chunk["embedding"])
        documents.append(chunk["text"])
        metadatas.append(metadata)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )


def run_ingestion_pipeline(techport_limit: int | None = 50) -> None:
    """End-to-end: fetch (multi-source) -> filter -> chunk -> embed -> store."""
    print("Preparing aggregated document chunks across all 4 categories...")
    chunks = prepare_all_chunks(techport_limit=techport_limit)
    print(f"Produced {len(chunks)} multi-category chunks")

    if not chunks:
        print("No document chunks produced.")
        return

    embedded_chunks = run_batch_embedding(chunks)
    print(f"Embedded {len(embedded_chunks)} chunks")

    store_chunks(embedded_chunks)
    print(f"Stored in ChromaDB collection '{COLLECTION_NAME}' at {CHROMA_PATH}")


if __name__ == "__main__":
    run_ingestion_pipeline(techport_limit=20)