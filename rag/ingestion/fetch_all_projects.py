import requests
import json


TECHPORT_BASE_URL = "https://techport.nasa.gov/api"

UPDATED_SINCE = "2025-01-01"

CANDIDATE_TX_PREFIXES = ("TX01", "TX04", "TX10", "TX17")

def fetch_all_projects() -> list[dict]:
    """GET /api/projects/search, return the list of result records."""

    response = requests.get (f"{TECHPORT_BASE_URL}/projects/search",
            params={'updatedSince' : UPDATED_SINCE},
             headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    data = response.json()
    results = response.json()["results"]

    print(list(data.keys()))

    for key , value in data.items():
        if key != "results":
            print(key, ":" , value)
    print("total:", data["total"])
    print("offset:", data["offset"])
    print("len(results):", len(data["results"]))
    return results

REPAIR_DROID_KEYWORDS = [
    "servicing", "repair", "docking", "rendezvous", "robotic arm",
    "grappling", "refueling", "debris", "osam", "rpo", "manipulator",
    "satellite life", "in-space servicing", "inspection", "proximity"
]

def filter_candidates(projects : list[dict]) -> list[dict]:
    """Filter projects matching candidate Taxonomy prefixes and Satellite Repair Droid keywords."""
    matches = []
    for project in projects:
        title = (project.get("title") or "").lower()
        description = (project.get("description") or "").lower()
        benefits = (project.get("benefits") or "").lower()
        combined_text = f"{title} {description} {benefits}"
        
        if not combined_text.strip():
            continue

        primary_code = (project.get("primaryTx") or {}).get("code", "") or ""
        tx_match = primary_code.startswith(CANDIDATE_TX_PREFIXES)
        kw_match = any(kw in combined_text for kw in REPAIR_DROID_KEYWORDS)

        if tx_match or kw_match:
            matches.append(project)

    return matches

if __name__ == "__main__":

    projects = fetch_all_projects()
    print(f"fetch_all_projects: {len(projects)} results")
    print(list(projects[0].keys()))
    print(projects[0].get("additionalTxs"))
    filtered = filter_candidates(projects)
    print(f"After filter_candidates (data-quality): {len(filtered)}")