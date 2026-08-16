import tiktoken

ENCODING = tiktoken.get_encoding("cl100k_base")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

TECHPORT_BASE_URL = "https://techport.nasa.gov/api"
TECHPORT_VIEW_URL = "https://techport.nasa.gov/view"

UPDATED_SINCE = "2025-01-01"
CANDIDATE_TX_PREFIXES = ("TX01", "TX04", "TX10", "TX17")

USER_AGENT = "OrbitalLocker/1.0 (ajay@orbitallocker.com)"

SEC_HEADERS = {
    "User-Agent": USER_AGENT
}

SPACE_BENCHMARKS = [
    {"name": "Northrop Grumman Corp", "cik": "0001133421", "symbol": "NOC"}
]

USPTO_API_URL = "https://api.patentsview.org/patents/query"

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

RSS_FEEDS = [
    {"name": "SpaceNews", "url": "https://spacenews.com/feed/"},
    {"name": "Payload Space", "url": "https://payloadspace.com/feed/"}
]
