from rag.ingestion.fetch_all_projects import fetch_all_projects, filter_candidates
from rag.ingestion.techport import build_project_document
from rag.ingestion.sec_edgar import fetch_all_financial_benchmarks
from rag.ingestion.patents import fetch_all_space_patents
from rag.ingestion.rss_market import fetch_all_market_news
from rag.ingestion.chunk import chunk_text, chunk_document

def collect_all_raw_documents(techport_limit: int | None = 50) -> list[dict]:
    """
    Aggregate documents from all 4 categories:
    1. Technical & TRL (NASA TechPort)
    2. Financial Intelligence (SEC EDGAR)
    3. Patents & Prior Art (USPTO)
    4. Market Intelligence (SpaceNews / Payload RSS)
    """
    all_docs = []
    
    # 1. Technical & TRL (NASA TechPort)
    print("Fetching NASA TechPort projects...")
    try:
        raw_techport = fetch_all_projects()
        filtered = filter_candidates(raw_techport)
        if techport_limit:
            filtered = filtered[:techport_limit]
        for p in filtered:
            text = build_project_document(p)
            p_id = p.get("projectId")
            all_docs.append({
                "source_id": f"TECHPORT_{p_id}",
                "title": p.get("title", ""),
                "text": text,
                "category": "Technical & TRL",
                "source": "NASA TechPort",
                "trl_current": p.get("trlCurrent"),
                "url": f"https://techport.nasa.gov/view/{p_id}" if p_id else ""
            })
    except Exception as e:
        print(f"Error collecting TechPort projects: {e}")

    # 2. Financial Intelligence (SEC EDGAR)
    print("Fetching Financial Intelligence (SEC EDGAR)...")
    all_docs.extend(fetch_all_financial_benchmarks())

    # 3. Patents & Prior Art (USPTO)
    print("Fetching Patents & Prior Art (USPTO)...")
    all_docs.extend(fetch_all_space_patents())

    # 4. Market Intelligence (RSS News)
    print("Fetching Market Intelligence (RSS)...")
    all_docs.extend(fetch_all_market_news())

    return all_docs

def prepare_all_chunks(techport_limit: int | None = 50) -> list[dict]:
    """Chunk all aggregated documents into 500-token windows."""
    docs = collect_all_raw_documents(techport_limit=techport_limit)
    all_chunks = []
    
    for doc in docs:
        text = doc["text"]
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "chunk_id": f"{doc['source_id']}_{i}",
                "source_id": doc["source_id"],
                "chunk_index": i,
                "text": chunk,
                "title": doc.get("title", ""),
                "category": doc.get("category", "General"),
                "source": doc.get("source", "Unknown"),
                "url": doc.get("url", ""),
                "trl_current": doc.get("trl_current")
            })
            
    print(f"Total aggregated chunks across all data sources: {len(all_chunks)}")
    return all_chunks

if __name__ == "__main__":
    chunks = prepare_all_chunks(techport_limit=10)
    print(f"Sample Chunk Output:\n", chunks[0] if chunks else "No chunks generated.")
