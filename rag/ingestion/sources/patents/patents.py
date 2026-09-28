import json
import requests

from rag.ingestion.config import USER_AGENT
from rag.ingestion.sources.patents.config import DEFAULT_SEARCH_KEYWORDS, PATENT_SOURCES
from rag.ingestion.utils import build_document_text, format_field_line


def _get_source_by_name(name: str) -> dict | None:
    for src in PATENT_SOURCES:
        if src.get("name") == name:
            return src
    return None


def fetch_patentsview_patents(keyword: str, limit: int = 5) -> list[dict]:
    """
    Query USPTO PatentsView API for space subsystem patents matching keyword.
    Requires registered API Key (X-Api-Key) as configured in PATENT_SOURCES.
    """
    source = _get_source_by_name("USPTO PatentsView")
    if not source:
        return []

    api_key = source.get("api_key", "")
    api_url = source.get("url", "https://search.patentsview.org/api/v1/patent/")

    if not api_key:
        print("PatentsView API key not configured. Skipping PatentsView query.")
        return []

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "X-Api-Key": api_key,
    }

    query = {"_text_phrase": {"patent_title": keyword}}
    fields = ["patent_id", "patent_number", "patent_title", "patent_date", "patent_abstract"]
    params = {
        "q": json.dumps(query),
        "f": json.dumps(fields),
        "o": json.dumps({"per_page": limit}),
    }

    try:
        response = requests.get(
            api_url,
            params=params,
            headers=headers,
            timeout=15,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("patents", data.get("data", []))
        elif response.status_code in (401, 403):
            print(f"PatentsView API authentication error (status {response.status_code}).")
        else:
            print(f"PatentsView API returned status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"PatentsView API query error for '{keyword}': {e}")

    return []


def fetch_nasa_sti_prior_art(keyword: str, limit: int = 5) -> list[dict]:
    """
    Query NASA STI (NTRS) citations API for aerospace prior art, technical papers,
    and subsystem patents matching keyword. (Public REST API, no auth required).
    """
    source = _get_source_by_name("NASA STI (NTRS)")
    api_url = source.get("url") if source else "https://ntrs.nasa.gov/api/citations/search"

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    params = {
        "q": keyword,
        "page": {"size": limit},
    }

    try:
        response = requests.get(
            api_url,
            params=params,
            headers=headers,
            timeout=15,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])
        else:
            print(f"NASA STI API returned status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"NASA STI API query error for '{keyword}': {e}")

    return []


def build_patent_document_text(patent: dict) -> str:
    """Format USPTO patent details into structured document text for embeddings."""
    title = patent.get("patent_title", "Space Technology Patent")
    p_num = patent.get("patent_id") or patent.get("patent_number", "N/A")
    date = patent.get("patent_date", "N/A")
    abstract = patent.get("patent_abstract", "No abstract available.")

    lines = [
        format_field_line("Title", f"Patent US{p_num} - {title}"),
        format_field_line("Patent Number", f"US{p_num}"),
        format_field_line("Issue Date", date),
        format_field_line("Category", "Patents & IP"),
        format_field_line("Subsystem Focus", "Aerospace & Orbital Mechanics"),
        format_field_line("Abstract", abstract),
    ]
    lines = [line for line in lines if line is not None]
    return build_document_text(lines)


def build_nasa_sti_document_text(item: dict) -> str:
    """Format NASA STI prior art / patent details into structured document text for embeddings."""
    title = item.get("title", "Aerospace Prior Art Document")
    doc_id = item.get("id", "N/A")
    date = item.get("distributionDate") or item.get("created") or "N/A"
    abstract = item.get("abstract", "No abstract available.")
    sti_type = item.get("stiTypeDetails") or item.get("stiType") or "Technical Prior Art"

    lines = [
        format_field_line("Title", title),
        format_field_line("Document ID", f"NASA-STI-{doc_id}"),
        format_field_line("Document Type", sti_type),
        format_field_line("Publication Date", str(date)[:10]),
        format_field_line("Category", "Patents & IP"),
        format_field_line("Subsystem Focus", "Aerospace Subsystems & Prior Art"),
        format_field_line("Abstract", abstract),
    ]
    lines = [line for line in lines if line is not None]
    return build_document_text(lines)


def fetch_all_space_patents(keywords: list[str] | None = None) -> list[dict]:
    """
    Fetch aerospace patents and subsystem prior art across configured sources
    in PATENT_SOURCES (NASA STI and USPTO PatentsView) matching search keywords.
    """
    search_keywords = keywords or DEFAULT_SEARCH_KEYWORDS
    results = []
    seen_ids = set()

    # 1. Fetch from NASA STI (NTRS) - active public API
    for kw in search_keywords:
        items = fetch_nasa_sti_prior_art(kw, limit=3)
        for item in items:
            item_id = item.get("id")
            if item_id and item_id not in seen_ids:
                seen_ids.add(item_id)
                doc_text = build_nasa_sti_document_text(item)
                results.append({
                    "id": f"NASA_STI_{item_id}",
                    "title": item.get("title", "NASA Prior Art"),
                    "text": doc_text,
                    "category": "Patents & IP",
                    "source": "NASA STI (NTRS)",
                    "url": f"https://ntrs.nasa.gov/citations/{item_id}",
                })

    # 2. Fetch from USPTO PatentsView if key configured
    for kw in search_keywords:
        patents = fetch_patentsview_patents(kw, limit=3)
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
                    "url": f"https://patents.google.com/patent/US{p_id}",
                })

    return results


if __name__ == "__main__":
    patents = fetch_all_space_patents()
    print(f"Fetched {len(patents)} patent / prior art documents.")
    if patents:
        print("Sample Patent / Prior Art Document:\n", patents[0]["text"])
