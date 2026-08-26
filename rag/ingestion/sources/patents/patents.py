import requests
import json
from rag.ingestion.config import USER_AGENT
from rag.ingestion.sources.patents.config import PATENTS_API_URL, PATENTS_API_KEY, DEFAULT_SEARCH_KEYWORDS
from rag.ingestion.utils import format_field_line, build_document_text


def fetch_patents_by_keyword(keyword: str, limit: int = 10) -> list[dict]:
    """
    Query PatentsView API v2 / USPTO Open Data API for space subsystem patents matching keyword.
    Requires registered API Key (X-Api-Key).
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
    if PATENTS_API_KEY:
        headers["X-Api-Key"] = PATENTS_API_KEY
        headers["X-API-KEY"] = PATENTS_API_KEY

    query = {"_text_phrase": {"patent_title": keyword}}
    fields = ["patent_id", "patent_number", "patent_title", "patent_date", "patent_abstract"]
    params = {
        "q": json.dumps(query),
        "f": json.dumps(fields),
        "o": json.dumps({"per_page": limit})
    }

    try:
        response = requests.get(
            PATENTS_API_URL,
            params=params,
            headers=headers,
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("patents", data.get("data", []))
        elif response.status_code in (401, 403):
            print(f"Patents API authentication required (status {response.status_code}). Please provide PATENTSVIEW_API_KEY / USPTO_API_KEY in .env.")
        else:
            print(f"Patents API returned status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"Patents API query error for '{keyword}': {e}")

    return []


def build_patent_document_text(patent: dict) -> str:
    """Format patent details into structured document text for embeddings using shared helpers."""
    title = patent.get("patent_title", "Space Technology Patent")
    p_num = patent.get("patent_id") or patent.get("patent_number", "N/A")
    date = patent.get("patent_date", "N/A")
    abstract = patent.get("patent_abstract", "No abstract available.")

    lines = [
        format_field_line("Title", f"Patent US{p_num} - {title}"),
        format_field_line("Patent Number", f"US{p_num}"),
        format_field_line("Issue Date", date),
        format_field_line("Category", "Patents & Prior Art"),
        format_field_line("Subsystem Focus", "Aerospace & Orbital Mechanics"),
        format_field_line("Abstract", abstract)
    ]
    lines = [line for line in lines if line is not None]
    return build_document_text(lines)


def fetch_all_space_patents() -> list[dict]:
    """Fetch space patents across default aerospace keywords from PatentsView API v2."""
    results = []
    seen_ids = set()

    for kw in DEFAULT_SEARCH_KEYWORDS:
        patents = fetch_patents_by_keyword(kw, limit=5)
        for p in patents:
            p_id = p.get("patent_id") or p.get("patent_number")
            if p_id and p_id not in seen_ids:
                seen_ids.add(p_id)
                doc_text = build_patent_document_text(p)
                results.append({
                    "id": f"PATENT_{p_id}",
                    "title": f"Patent US{p_id}: {p.get('patent_title', '')}",
                    "text": doc_text,
                    "category": "Patents & IP",
                    "source": "USPTO PatentsView",
                    "url": f"https://patents.google.com/patent/US{p_id}"
                })

    return results


if __name__ == "__main__":
    patents = fetch_all_space_patents()
    print(f"Fetched {len(patents)} live patent documents.")
    if patents:
        print("Sample Patent Document:\n", patents[0]["text"])
