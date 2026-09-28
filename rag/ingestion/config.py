import tiktoken

ENCODING = tiktoken.get_encoding("cl100k_base")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

USER_AGENT = "OrbitalLocker/1.0 (ajay@orbitallocker.com)"

# Drops oversized/repetitive "sponge" docs before chunking (see utils.py::filter_oversized_documents).
MAX_DOCUMENT_TOKENS = 20_000
MIN_UNIQUE_WORD_RATIO = 0.05

# Hash for detecting post-ingestion chunk tampering (see utils.py::add_content_hashes).
CONTENT_HASH_ALGORITHM = "sha256"

DEFAULT_RAG_CATEGORIES = [
    "Technical & TRL",
    "Financial Intelligence",
    "Patents & IP",
    "Market Intelligence",
]


def get_default_categories() -> list[str]:
    """Return the baseline list of registered RAG domain categories."""
    return list(DEFAULT_RAG_CATEGORIES)

