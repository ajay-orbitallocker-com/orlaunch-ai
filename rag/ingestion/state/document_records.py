from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from rag.corpus.document_types import DocumentType
from rag.corpus.categories import TrustTier
from rag.corpus.document_types import DocumentType

# Values must match the CHECK constraints in db/migrations/001_corpus_schema.sql.
class DocumentStatus(str, Enum):
    """Where a document stands in the corpus."""

    ACTIVE = "active"              # searchable
    DUPLICATE = "duplicate"        # near-copy of another document; not indexed
    SUPERSEDED = "superseded"      # replaced by a newer version of itself
    REMOVED = "removed"            # gone from the source; chunks deleted
    REJECTED = "rejected"          # failed validation; never indexed
    QUARANTINED = "quarantined"    # failed repeatedly; skipped until reviewed


class RejectionReason(str, Enum):
    """Why validation refused a document."""

    OVERSIZED = "oversized"
    REPETITIVE = "repetitive"
    INJECTION_SUSPECTED = "injection_suspected"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    UNSUPPORTED_FORMAT = "unsupported_format"


class ErrorCode(str, Enum):
    """Which ingestion stage failed; codes only, never error text."""

    FETCH_FAILED = "fetch_failed"
    FETCH_TIMEOUT = "fetch_timeout"
    PARSE_FAILED = "parse_failed"
    EMBED_FAILED = "embed_failed"
    WRITE_FAILED = "write_failed"


@dataclass(frozen=True)
class DocumentRecord:
    """What ingestion keeps in memory of one row of corpus documents."""

    document_id: str
    source_name: str
    document_type: DocumentType
    title: str
    url: str
    published_at: datetime | None
    content_hash: str                           # SHA-256 of the normalised content
    processing_version: str                     # chunker and header version that produced its chunks
    status: DocumentStatus
    similarity_fingerprint: int | None = None   # SimHash, for near-duplicate checks
    duplicate_of_document_id: str | None = None
    rejection_reason: RejectionReason | None = None
    failed_attempts: int = 0
    last_error_code: ErrorCode | None = None
    first_seen_at: datetime | None = None       # set by the database on first insert
    last_seen_at: datetime | None = None        # updated every run the source still lists it
