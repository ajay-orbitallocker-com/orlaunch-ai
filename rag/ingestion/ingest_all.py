from rag.ingestion.sources.techport.techport import fetch_all_projects, filter_candidates, build_techport_documents
from rag.ingestion.chunk import chunk_documents_by_category
from rag.ingestion.sources.sec_edgar.sec_edgar import fetch_all_financial_benchmarks
from rag.ingestion.sources.patents.patents import fetch_all_space_patents
from rag.ingestion.sources.rss_market.rss_market import fetch_all_market_news
from rag.ingestion.utils import add_content_hashes, filter_oversized_documents
from rag.embeddings.batch import run_batch_embedding, run_sync_embedding
from rag.embeddings.embed_and_store import store_chunks


# ---------------------------------------------------------------------------
# TechPort - no changes to be made
# ---------------------------------------------------------------------------

def fetch_techport_documents() -> list[dict]:
    """
    Fetch, filter, and build TechPort documents in the common document shape.

    Returns:
        list[dict] in the common shape: {"id", "text", "title", "category",
        "source", "trl_current", "url"}. Keyed "id" (not "source_id")
    """
    projects = filter_candidates(fetch_all_projects())
    return build_techport_documents(projects)


# ---------------------------------------------------------------------------
# SEC / Patents / RSS — Connected Fetchers
# ---------------------------------------------------------------------------

def fetch_sec_documents() -> list[dict]:
    """
    Fetch financial benchmark documents from SEC EDGAR.
    """
    return fetch_all_financial_benchmarks()


def fetch_patent_documents() -> list[dict]:
    """
    Fetch patent prior art documents from USPTO / database.
    """
    return fetch_all_space_patents()


def fetch_market_documents() -> list[dict]:
    """
    Fetch market intelligence news documents from RSS feeds.
    """
    return fetch_all_market_news()


# ---------------------------------------------------------------------------
# Orchestration — done. Loops over all 4 sources uniformly; placeholders
# above will print a caught error until completed
# ---------------------------------------------------------------------------

def collect_all_raw_documents() -> list[dict]:
    """
    Aggregate documents from all 4 categories:
    1. Technical & TRL (NASA TechPort)
    2. Financial Intelligence (SEC EDGAR)
    3. Patents & Prior Art (USPTO)
    4. Market Intelligence (SpaceNews / Payload RSS)

    Each source is a zero-arg fetch function returning documents in the
    common shape ({"id", "text", "category", ...}). One try/except wraps
    every source uniformly, so one source failing (including an
    unimplemented placeholder) doesn't abort the others.

    Returns:
        list[dict] of raw documents, combined across all 4 sources.
    """
    sources = [
        ("NASA TechPort", fetch_techport_documents),
        ("SEC EDGAR", fetch_sec_documents),
        ("USPTO Patents", fetch_patent_documents),
        ("RSS Market News", fetch_market_documents),
    ]

    all_docs = []
    for label, fetch_fn in sources:
        print(f"Fetching {label}...")
        try:
            all_docs.extend(fetch_fn())
        except Exception as e:
            print(f"Error collecting {label}: {e}")

    return all_docs


def prepare_all_chunks() -> list[dict]:
    """
    Fetch and chunk all aggregated documents, using the shared category-aware
    chunker so each source's category-appropriate splitter (prose vs.
    line-boundary) is applied automatically via CATEGORY_CHUNK_CONFIG.

    Returns:
        list[dict] of chunk dicts: {"id", "chunk_index", "text",
        ...passthrough fields from the source document}.
    """
    docs = collect_all_raw_documents()
    docs = filter_oversized_documents(docs)
    chunks = chunk_documents_by_category(docs)
    chunks = add_content_hashes(chunks)

    print(f"Total aggregated chunks across all data sources: {len(chunks)}")
    return chunks


def run_ingestion_pipeline_all() -> None:
    """
    End-to-end multi-source pipeline: chunk -> embed -> store across all 4 categories.
    """
    print("Preparing aggregated document chunks across all 4 categories...")
    chunks = prepare_all_chunks()
    print(f"Produced {len(chunks)} multi-category chunks")

    if not chunks:
        print("No document chunks produced.")
        return

    embedded_chunks = run_batch_embedding(chunks)
    print(f"Embedded {len(embedded_chunks)} chunks")

    store_chunks(embedded_chunks)
    print("Multi-source ingestion pipeline complete.")


def clean_legacy_unidentified_chunks() -> int:
    """Delete legacy chunks that were stored with id=None in ChromaDB."""
    from chroma_config import collection
    data = collection.get(include=["metadatas"])
    corrupted_ids = [
        doc_id for doc_id, meta in zip(data["ids"], data["metadatas"])
        if not meta or meta.get("id") is None
    ]
    if corrupted_ids:
        collection.delete(ids=corrupted_ids)
        print(f"Cleaned up {len(corrupted_ids)} legacy chunks with id=None from ChromaDB.")
    return len(corrupted_ids)


def ingest_small_sources_sync() -> None:
    """
    Synchronously ingest, chunk, embed, and store small sources
    (SEC EDGAR, USPTO Patents, RSS Market News) directly into ChromaDB.
    Avoids waiting on the 24-hr batch API and ensures all 4 categories
    have fresh, valid chunks with proper IDs in ChromaDB.
    """
    sources = [
        ("SEC EDGAR", fetch_sec_documents),
        ("USPTO Patents", fetch_patent_documents),
        ("RSS Market News", fetch_market_documents),
    ]

    all_docs = []
    for label, fetch_fn in sources:
        print(f"Fetching {label}...")
        try:
            docs = fetch_fn()
            print(f"  Fetched {len(docs)} documents from {label}.")
            all_docs.extend(docs)
        except Exception as e:
            print(f"Error collecting {label}: {e}")

    if not all_docs:
        print("No documents collected from small sources.")
        return

    all_docs = filter_oversized_documents(all_docs)

    print(f"\nChunking {len(all_docs)} small source documents by category...")
    chunks = chunk_documents_by_category(all_docs)
    chunks = add_content_hashes(chunks)
    print(f"Produced {len(chunks)} chunks.")

    print(f"\nRunning synchronous embedding via OpenAI text-embedding-3-small...")
    embedded_chunks = run_sync_embedding(chunks)
    print(f"Successfully embedded {len(embedded_chunks)} chunks.")

    if embedded_chunks:
        store_chunks(embedded_chunks)
        print("Small sources sync ingestion complete and stored in ChromaDB.")


if __name__ == "__main__":
    run_ingestion_pipeline_all()
