import requests
import json

USPTO_API_URL = "https://api.patentsview.org/patents/query"

DEFAULT_SEARCH_KEYWORDS = [
    "orbital maneuvering",
    "cubesat propulsion",
    "satellite refueling",
    "autonomous Rendezvous"
]

def fetch_patents_by_keyword(keyword: str, limit: int = 10) -> list[dict]:
    """Query USPTO PatentsView API for space subsystem patents."""
    query = {"_text_any": {"patent_title": keyword}}
    fields = ["patent_number", "patent_title", "patent_date", "patent_abstract"]
    options = {"per_page": limit}
    
    headers = {"User-Agent": "OrbitalLocker/1.0 (ajaykumaravula999@gmail.com)"}
    
    try:
        response = requests.post(
            USPTO_API_URL,
            json={"q": query, "f": fields, "o": options},
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("patents", [])
    except Exception as e:
        print(f"USPTO API query error for '{keyword}': {e}")
        
    return []

def build_patent_document_text(patent: dict) -> str:
    """Format patent details into structured document text for embeddings."""
    title = patent.get("patent_title", "Space Technology Patent")
    p_num = patent.get("patent_number", "N/A")
    date = patent.get("patent_date", "N/A")
    abstract = patent.get("patent_abstract", "No abstract available.")
    
    lines = [
        f"Title: Patent US{p_num} - {title}",
        f"Patent Number: US{p_num}",
        f"Issue Date: {date}",
        "Category: Patents & Prior Art",
        "Subsystem Focus: Aerospace & Orbital Mechanics",
        f"Abstract: {abstract}"
    ]
    return "\n".join(lines)

def fetch_all_space_patents() -> list[dict]:
    """Fetch space patents across default aerospace keywords."""
    results = []
    seen_ids = set()
    
    for kw in DEFAULT_SEARCH_KEYWORDS:
        patents = fetch_patents_by_keyword(kw, limit=5)
        for p in patents:
            p_id = p.get("patent_number")
            if p_id and p_id not in seen_ids:
                seen_ids.add(p_id)
                doc_text = build_patent_document_text(p)
                results.append({
                    "source_id": f"PATENT_{p_id}",
                    "title": f"Patent US{p_id}: {p.get('patent_title', '')}",
                    "text": doc_text,
                    "category": "Patents & IP",
                    "source": "USPTO PatentsView",
                    "url": f"https://patents.google.com/patent/US{p_id}"
                })
    return results

if __name__ == "__main__":
    patents = fetch_all_space_patents()
    print(f"Successfully fetched {len(patents)} patent prior-art documents.")
    if patents:
        print("Sample Patent Document:\n", patents[0]["text"])
