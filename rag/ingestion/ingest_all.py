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

def get_source_registry():
    """Registry of all data sources and their fetch functions."""
    return [
        ("NASA TechPort", fetch_techport_documents),
        ("SEC EDGAR", fetch_sec_documents),
        ("USPTO Patents", fetch_patent_documents),
        ("RSS Market News", fetch_market_documents),
    ]


def collect_all_raw_documents(selected_sources: list[str] | None = None) -> list[dict]:
    """
    Aggregate documents from registered categories:
    1. Technical & TRL (NASA TechPort)
    2. Financial Intelligence (SEC EDGAR)
    3. Patents & IP (NASA STI / USPTO Patents)
    4. Market Intelligence (SpaceNews / Payload RSS)

    Args:
        selected_sources: Optional list of source names to ingest (e.g. ["SEC EDGAR", "USPTO Patents"]).
                         If None, ingests from all registered sources.

    Returns:
        list[dict] of raw documents across selected sources.
    """
    registry = get_source_registry()
    if selected_sources:
        selected_lower = {s.lower() for s in selected_sources}
        registry = [
            (label, fn) for label, fn in registry
            if label.lower() in selected_lower or any(s in label.lower() for s in selected_lower)
        ]

    all_docs = []
    for label, fetch_fn in registry:
        print(f"Fetching {label}...")
        try:
            docs = fetch_fn()
            print(f"  Fetched {len(docs)} documents from {label}.")
            all_docs.extend(docs)
        except Exception as e:
            print(f"Error collecting {label}: {e}")

    return all_docs


def prepare_all_chunks(selected_sources: list[str] | None = None) -> list[dict]:
    """
    Fetch and chunk all aggregated documents, using the shared category-aware
    chunker so each source's category-appropriate splitter (prose vs.
    line-boundary) is applied automatically via CATEGORY_CHUNK_CONFIG.

    Returns:
        list[dict] of chunk dicts: {"id", "chunk_index", "text",
        ...passthrough fields from the source document}.
    """
    docs = collect_all_raw_documents(selected_sources=selected_sources)
    docs = filter_oversized_documents(docs)
    chunks = chunk_documents_by_category(docs)
    chunks = add_content_hashes(chunks)

    print(f"Total aggregated chunks across selected data sources: {len(chunks)}")
    return chunks


def run_ingestion_pipeline_all(
    selected_sources: list[str] | None = None,
    sync_embedding: bool = False
) -> None:
    """
    End-to-end multi-source pipeline: collect -> chunk -> embed -> store.

    Args:
        selected_sources: Optional list of source labels to run.
        sync_embedding: If True, uses run_sync_embedding directly (useful for small batches).
                        If False, uses run_batch_embedding (OpenAI Batch API).
    """
    print("Preparing aggregated document chunks across data sources...")
    chunks = prepare_all_chunks(selected_sources=selected_sources)
    print(f"Produced {len(chunks)} multi-category chunks")

    if not chunks:
        print("No document chunks produced.")
        return

    if sync_embedding:
        print(f"Running synchronous embedding for {len(chunks)} chunks via OpenAI text-embedding-3-small...")
        embedded_chunks = run_sync_embedding(chunks)
    else:
        print(f"Submitting batch embedding for {len(chunks)} chunks...")
        embedded_chunks = run_batch_embedding(chunks)

    print(f"Embedded {len(embedded_chunks)} chunks")
    store_chunks(embedded_chunks)
    print("Multi-source ingestion pipeline complete.")

if __name__ == "__main__":
    run_ingestion_pipeline_all()

