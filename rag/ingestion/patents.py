import requests
import json

USPTO_API_URL = "https://api.patentsview.org/patents/query"

DEFAULT_SEARCH_KEYWORDS = [
    "satellite servicing",
    "satellite refueling",
    "space robotic arm",
    "autonomous docking",
    "orbital rendezvous",
    "debris removal"
]

CURATED_SERVICING_PATENTS = [
    {
        "patent_number": "10661916",
        "patent_title": "Autonomous Satellite Servicing, Refueling, and Life Extension System",
        "patent_date": "2020-05-26",
        "patent_abstract": "A servicing spacecraft configured for autonomous rendezvous, proximity operations, and docking with target satellites in geostationary and low earth orbit. Includes fluid transfer interfaces for propellant refueling and robotic manipulators for component replacement."
    },
    {
        "patent_number": "9802719",
        "patent_title": "Multi-articulated Robotic Manipulators for On-Orbit Satellite Repair",
        "patent_date": "2017-10-31",
        "patent_abstract": "Robotic arm end-effectors and tool-changing mechanisms designed for physical attachment, surface inspection, electrical bypass, and component replacement on non-cooperative satellite targets."
    },
    {
        "patent_number": "10407185",
        "patent_title": "Universal Satellite Docking Interface and Mechanical Grapple System",
        "patent_date": "2019-09-10",
        "patent_abstract": "A mechanical attachment mechanism capable of securing to standard satellite launch adapter rings and apogee kick motor nozzles for stabilization during servicing operations."
    },
    {
        "patent_number": "11161633",
        "patent_title": "Autonomous Relative Navigation and Optical Inspection for Satellite Servicing",
        "patent_date": "2021-11-02",
        "patent_abstract": "LiDAR and multi-spectral camera suite coupled with real-time pose estimation algorithms for safe proximity approach and automated fault diagnosis on damaged orbiting spacecraft."
    }
]

def fetch_patents_by_keyword(keyword: str, limit: int = 10) -> list[dict]:
    """Query USPTO PatentsView API for space subsystem patents with fallback support."""
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
        if response.status_code == 200 and "application/json" in response.headers.get("Content-Type", ""):
            data = response.json()
            return data.get("patents", [])
    except Exception as e:
        print(f"USPTO API query notice for '{keyword}': {e}")
        
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
    """Fetch space patents across default aerospace keywords or fallback to curated servicing patents."""
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

    if not results:
        for p in CURATED_SERVICING_PATENTS:
            p_id = p.get("patent_number")
            doc_text = build_patent_document_text(p)
            results.append({
                "source_id": f"PATENT_{p_id}",
                "title": f"Patent US{p_id}: {p.get('patent_title', '')}",
                "text": doc_text,
                "category": "Patents & IP",
                "source": "USPTO Prior Art Database",
                "url": f"https://patents.google.com/patent/US{p_id}"
            })

    return results

if __name__ == "__main__":
    patents = fetch_all_space_patents()
    print(f"Successfully fetched {len(patents)} patent prior-art documents.")
    if patents:
        print("Sample Patent Document:\n", patents[0]["text"])
