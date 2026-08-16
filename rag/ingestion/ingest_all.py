from rag.ingestion.fetch_all_projects import fetch_all_projects, filter_candidates
from rag.ingestion.techport import build_techport_documents
from rag.ingestion.chunk import chunk_documents_by_category


# ---------------------------------------------------------------------------
# TechPort 
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
# SEC / Patents / RSS — PLACEHOLDERS for Ajay to complete.
#
# Each should end up calling the matching fetch_all_x() already written in
# sec_edgar.py / patents.py / rss_market.py, once those return documents
# keyed "id" (not "source_id") in the same common shape TechPort uses above
# — that's what lets chunk_documents_by_category() below work uniformly
# across all 4 sources.
#

# ---------------------------------------------------------------------------

def fetch_sec_documents() -> list[dict]:
    """
    PLACEHOLDER — Ajay to complete.

    Should call fetch_all_financial_benchmarks() from sec_edgar.py, once that
    file's documents are keyed "id" instead of "source_id".

    Takes: nothing.
    Returns: list[dict] in the common document shape (see
        fetch_techport_documents() above for the exact shape).
    """
    raise NotImplementedError("Wire up sec_edgar.py's fetch_all_financial_benchmarks() here")


def fetch_patent_documents() -> list[dict]:
    """
    PLACEHOLDER — Ajay to complete.

    Should call fetch_all_space_patents() from patents.py, once that file's
    documents are keyed "id" instead of "source_id".

    Takes: nothing.
    Returns: list[dict] in the common document shape.
    """
    raise NotImplementedError("Wire up patents.py's fetch_all_space_patents() here")


def fetch_market_documents() -> list[dict]:
    """
    PLACEHOLDER — Ajay to complete.

    Should call fetch_all_market_news() from rss_market.py, once that file's
    documents are keyed "id" instead of "source_id" with a stable id (not
    Python's hash(link), which changes across runs).

    Takes: nothing.
    Returns: list[dict] in the common document shape.
    """
    raise NotImplementedError("Wire up rss_market.py's fetch_all_market_news() here")


# ---------------------------------------------------------------------------
# Orchestration — done. Loops over all 4 sources uniformly; placeholders
# above will print a caught error until Ajay completes them.
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
    PLACEHOLDER — not implemented yet. This is where embedding + storage for
    the multi-source pipeline should eventually happen.

    Goal: this function should end up being the multi-source version of
    embed_and_store.py::run_ingestion_pipeline() — i.e. chunk -> embed ->
    store, but for documents aggregated across all 4 sources instead of
    just TechPort.

    Takes:
        techport_limit : passed through to prepare_all_chunks().

    Returns:
        None. Once implemented, its side effect should be writing embedded
        chunks into the ChromaDB collection (same as
        embed_and_store.py::run_ingestion_pipeline() already does for
        TechPort).

    What needs to happen before this can be implemented, in order:

    1. Finish the 3 placeholder functions above (fetch_sec_documents(),
       fetch_patent_documents(), fetch_market_documents()) so
       collect_all_raw_documents() actually returns SEC/patent/RSS
       documents, not just TechPort's.

    2. DONE — batch.py and embed_and_store.py::store_chunks() have been
       generalized to key chunks by "id" instead of "project_id" (matching
       chunk_documents_by_category()'s output), so run_batch_embedding()
       can now be called directly on chunks from any source, TechPort
       included. No adapter needed here anymore.

    3. embed_and_store.py's build_metdata() still only knows how to build
       metadata for TechPort projects (it reads TechPort-specific fields
       and looks documents up by project id). A source-agnostic version of
       this is still needed before chunks from SEC/patents/RSS can
       actually be written to ChromaDB with correct metadata.

    Once 1-3 are done, this function's body should look very close to
    embed_and_store.py::run_ingestion_pipeline() — chunks =
    prepare_all_chunks(...), then run_batch_embedding(chunks), then store.
    """
    prepare_all_chunks(techport_limit=techport_limit)
    raise NotImplementedError(
        "Multi-source embedding/storage isn't wired yet — see this "
        "function's docstring for the 3 steps needed before it can be."
    )


if __name__ == "__main__":
    chunks = prepare_all_chunks(techport_limit=10)
    print(f"Sample Chunk Output:\n", chunks[0] if chunks else "No chunks generated.")
