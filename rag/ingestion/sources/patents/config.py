import os

PATENTS_API_KEY = os.getenv("PATENTSVIEW_API_KEY") or os.getenv("USPTO_API_KEY", "")
PATENTS_API_URL = os.getenv(
    "PATENTSVIEW_API_URL",
    os.getenv("USPTO_API_URL", "https://api.uspto.gov/api/v1/patent/search")
)

DEFAULT_SEARCH_KEYWORDS = [
    "satellite servicing",
    "satellite refueling",
    "space robotic arm",
    "autonomous docking",
    "orbital rendezvous",
    "robotic repair",
    "grappling mechanism",
    "debris removal"
]
