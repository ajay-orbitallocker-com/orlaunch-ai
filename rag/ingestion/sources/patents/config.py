import os

# Registered Patent and Aerospace Prior Art API Sources
PATENT_SOURCES = [
    {
        "name": "NASA STI (NTRS)",
        "url": "https://ntrs.nasa.gov/api/citations/search",
        "description": "NASA Technical Reports Server - aerospace patents, research, and subsystem prior art",
        "requires_auth": False,
    },
    {
        "name": "USPTO PatentsView",
        "url": os.getenv("PATENTSVIEW_API_URL", "https://search.patentsview.org/api/v1/patent/"),
        "description": "USPTO PatentsView API for patent search and abstracts",
        "requires_auth": True,
        "auth_header": "X-Api-Key",
        "api_key": os.getenv("PATENTSVIEW_API_KEY", ""),
    },
    {
        "name": "USPTO Open Data Portal",
        "url": os.getenv("USPTO_API_URL", "https://api.uspto.gov/api/v1/patent/search"),
        "description": "USPTO Open Data Portal Patent Search",
        "requires_auth": True,
        "auth_header": "X-API-KEY",
        "api_key": os.getenv("USPTO_API_KEY", ""),
    },
]

DEFAULT_SEARCH_KEYWORDS = [
    "satellite servicing",
    "satellite refueling",
    "space robotic arm",
    "autonomous docking",
    "orbital rendezvous",
    "robotic repair",
    "grappling mechanism",
    "debris removal",
]

