import hashlib
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from rag.ingestion.config import ENCODING, MAX_DOCUMENT_TOKENS, MIN_UNIQUE_WORD_RATIO


def strip_html(text: str) -> str:
    """Minimal HTML-to-text cleanup for description/benefits fields."""

    if not text:
        return ""

    return BeautifulSoup(text, "html.parser").get_text(separator=" ", strip=True)


def format_field_line(label: str, value) -> str | None:
    """Format a single 'Label : value' line, or None if value is empty."""

    if not value:
        return None

    return f"{label} : {value}"


def build_document_text(lines: list[str]) -> str:
    """Join already-formatted label lines into one text block."""

    return "\n".join(lines)


def _document_reject_reason(text: str) -> str | None:
    """
    Returns a reason string if `text` looks like an oversized or
    pathologically repetitive ("sponge") document, else None. Token count
    uses the same cl100k_base ENCODING as chunk.py, so the cap lines up
    with how chunk_size is already measured elsewhere in this package.
    """
    if not text:
        return None

    token_count = len(ENCODING.encode(text))
    if token_count > MAX_DOCUMENT_TOKENS:
        return f"exceeds {MAX_DOCUMENT_TOKENS}-token document cap ({token_count} tokens)"

    words = text.split()
    if len(words) >= 200:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < MIN_UNIQUE_WORD_RATIO:
            return f"pathologically repetitive content (unique-word ratio {unique_ratio:.3f} < {MIN_UNIQUE_WORD_RATIO})"

    return None


def filter_oversized_documents(documents: list[dict]) -> list[dict]:
    """
    Drops documents that are oversized or pathologically repetitive before
    they reach chunking/embedding. Applied once across all sources in
    ingest_all.py, so no per-source builder needs to remember to call this
    individually.
    """
    kept = []
    for document in documents:
        reason = _document_reject_reason(document.get("text", ""))
        if reason:
            print(f"Dropping document {document.get('id', '(no id)')} from ingestion - {reason}")
            continue
        kept.append(document)
    return kept


def compute_chunk_content_hash(chunk: dict, ingested_at: str) -> str:
    """
    Hashes (chunk id + chunk_index + raw chunk text + ingestion timestamp) so
    a later mutation of the stored chunk text (e.g. a number silently edited
    post-ingestion) changes the hash and is detectable on re-audit against
    the stored baseline. chunk_index is folded in alongside id because id
    alone is doc-level, not chunk-unique (every chunk of one parent document
    shares it - see chunk.py::chunk_documents) - id+chunk_index is already
    the compound identity embed_and_store.py uses for ChromaDB ids, so the
    hash binds to that same identity.
    """
    payload = f"{chunk.get('id', '')}|{chunk.get('chunk_index', '')}|{chunk.get('text', '')}|{ingested_at}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def add_content_hashes(chunks: list[dict], ingested_at: str | None = None) -> list[dict]:
    """
    Stamps each chunk dict with "ingested_at" and "content_hash" in place.
    One shared ingested_at timestamp per call (i.e. per ingestion run), not
    per chunk, so a run is one auditable boundary to diff against later -
    computed once here if not supplied by the caller.
    """
    ingested_at = ingested_at or datetime.now(timezone.utc).isoformat()
    for chunk in chunks:
        chunk["ingested_at"] = ingested_at
        chunk["content_hash"] = compute_chunk_content_hash(chunk, ingested_at)
    return chunks
