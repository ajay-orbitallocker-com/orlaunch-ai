"""What ingestion can ask of its state, split by who asks: the run (sources) and the pipeline (documents)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from rag.corpus.documents import Section
from rag.ingestion.sources.definitions import SourceDefinition
from rag.ingestion.state.document_records import DocumentRecord, ErrorCode


class SourceStateInterface(Protocol):
    """Sources, pauses and cursors; used by the run command. Implemented by SourceState."""

    def sync_sources(self, definitions: Sequence[SourceDefinition]) -> None:
        """Write the declared sources into corpus.sources; run at startup."""

    def is_paused(self, source_name: str) -> bool:
        """True if the source has been paused; a paused source is not fetched."""

    def get_cursor(self, source_name: str) -> str | None:
        """Where the last successful run stopped; None on a source's first run."""

    def save_cursor(self, source_name: str, cursor_value: str) -> None:
        """Move the cursor forward; call only after a run succeeds."""


class DocumentStateInterface(Protocol):
    """Document records; used by change detection, duplicates and write. Implemented by DocumentState."""

    def get_documents(self, document_ids: Sequence[str]) -> dict[str, DocumentRecord]:
        """Known records for these documents; IDs never seen before are absent."""

    def save_document(self, record: DocumentRecord, parent_sections: Sequence[Section]) -> None:
        """Insert or update a document and its full sections together, or neither."""

    def find_near_duplicates(self, fingerprint: int, max_distance: int, exclude_document_id: str) -> list[str]:
        """Active documents whose fingerprint differs by at most max_distance bits."""

    def mark_seen(self, document_ids: Sequence[str], seen_at: datetime) -> None:
        """Record that the source still lists these documents."""

    def record_failure(self, document_id: str, error_code: ErrorCode) -> int:
        """Count a failed attempt; returns the document's total failed attempts."""