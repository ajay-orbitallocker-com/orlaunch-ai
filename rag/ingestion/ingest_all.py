from rag.ingestion.fetch_all_projects import fetch_all_projects, filter_candidates
from rag.ingestion.techport import build_techport_documents
from rag.ingestion.chunk import chunk_documents_by_category
from rag.ingestion.sec_edgar import fetch_all_financial_benchmarks
from rag.ingestion.patents import fetch_all_space_patents
from rag.ingestion.rss_market import fetch_all_market_news
from rag.embeddings.batch import run_batch_embedding
from rag.embeddings.embed_and_store import store_chunks


# ---------------------------------------------------------------------------
# TechPort - no changes to be made
# ---------------------------------------------------------------------------

def fetch_techport_documents(techport_limit: int | None = 50) -> list[dict]:
    """
    Fetch, filter, and build TechPort documents in the common document shape.

    Takes:
        techport_limit : optional cap on number of TechPort projects to
            include (applied after filter_candidates()). None means no cap.

    Returns:
        list[dict] in the common shape: {"id", "text", "title", "category",
        "source", "trl_current", "url"}. Keyed "id" (not "source_id") 
    """
    projects = filter_candidates(fetch_all_projects())
    if techport_limit:
        projects = projects[:techport_limit]
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

def collect_all_raw_documents(techport_limit: int | None = 50) -> list[dict]:
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

    Takes:
        techport_limit : passed through to fetch_techport_documents().

    Returns:
        list[dict] of raw documents, combined across all 4 sources.
    """
    sources = [
        ("NASA TechPort", lambda: fetch_techport_documents(techport_limit)),
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


def prepare_all_chunks(techport_limit: int | None = 50) -> list[dict]:
    """
    Fetch and chunk all aggregated documents, using the shared category-aware
    chunker so each source's category-appropriate splitter (prose vs.
    line-boundary) is applied automatically via CATEGORY_CHUNK_CONFIG.

    Takes:
        techport_limit : passed through to collect_all_raw_documents().

    Returns:
        list[dict] of chunk dicts: {"id", "chunk_index", "text",
        ...passthrough fields from the source document}.
    """
    docs = collect_all_raw_documents(techport_limit=techport_limit)
    chunks = chunk_documents_by_category(docs)

    print(f"Total aggregated chunks across all data sources: {len(chunks)}")
    return chunks


def run_ingestion_pipeline_all(techport_limit: int | None = 50) -> None:
    """
    End-to-end multi-source pipeline: chunk -> embed -> store across all 4 categories.
    """
    print("Preparing aggregated document chunks across all 4 categories...")
    chunks = prepare_all_chunks(techport_limit=techport_limit)
    print(f"Produced {len(chunks)} multi-category chunks")

    if not chunks:
        print("No document chunks produced.")
        return

    embedded_chunks = run_batch_embedding(chunks)
    print(f"Embedded {len(embedded_chunks)} chunks")

    store_chunks(embedded_chunks)
    print("Multi-source ingestion pipeline complete.")


if __name__ == "__main__":
    chunks = prepare_all_chunks(techport_limit=10)
    print(f"Sample Chunk Output:\n", chunks[0] if chunks else "No chunks generated.")
