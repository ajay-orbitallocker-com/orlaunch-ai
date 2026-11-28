"""Document records and their full sections, stored in the corpus schema in Postgres."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

import psycopg

from rag.corpus.document_types import DocumentType
from rag.corpus.documents import Section
from rag.ingestion.state.document_records import DocumentRecord, DocumentStatus, ErrorCode, RejectionReason

# Column order shared by every SELECT and by _record_from_row.
_DOCUMENT_COLUMNS = """
    document_id, source_name, document_type, title, url, published_at, content_hash,
    processing_version, status, similarity_fingerprint, duplicate_of_document_id,
    rejection_reason, failed_attempts, last_error_code, first_seen_at, last_seen_at
"""

_TWO_TO_64 = 1 << 64


def _to_signed(fingerprint: int) -> int:
    """Unsigned 64-bit SimHash to the signed range Postgres bigint can hold."""
    return fingerprint - _TWO_TO_64 if fingerprint >= 1 << 63 else fingerprint


def _to_unsigned(stored: int) -> int:
    """Back from bigint to the unsigned SimHash the code compares."""
    return stored + _TWO_TO_64 if stored < 0 else stored


def _record_from_row(row: tuple) -> DocumentRecord:
    """One corpus.documents row, in _DOCUMENT_COLUMNS order, as a DocumentRecord."""
    return DocumentRecord(
        document_id=row[0],
        source_name=row[1],
        document_type=DocumentType(row[2]),
        title=row[3],
        url=row[4],
        published_at=row[5],
        content_hash=row[6],
        processing_version=row[7],
        status=DocumentStatus(row[8]),
        similarity_fingerprint=_to_unsigned(row[9]) if row[9] is not None else None,
        duplicate_of_document_id=row[10],
        rejection_reason=RejectionReason(row[11]) if row[11] else None,
        failed_attempts=row[12],
        last_error_code=ErrorCode(row[13]) if row[13] else None,
        first_seen_at=row[14],
        last_seen_at=row[15],
    )


class DocumentState:
    """Implements DocumentStateInterface; each write commits on its own."""

    def __init__(self, connection: psycopg.Connection) -> None:
        self._connection = connection   # opened by startup, closed by whoever opened it

    def get_documents(self, document_ids: Sequence[str]) -> dict[str, DocumentRecord]:
        """Known records for these documents; IDs never seen before are absent."""
        if not document_ids:
            return {}
        rows = self._connection.execute(
            f"SELECT {_DOCUMENT_COLUMNS} FROM corpus.documents WHERE document_id = ANY(%s)",
            (list(document_ids),),
        ).fetchall()
        return {row[0]: _record_from_row(row) for row in rows}

    def save_document(self, record: DocumentRecord, parent_sections: Sequence[Section]) -> None:
        """Insert or update a document and its full sections together, or neither."""
        fingerprint = _to_signed(record.similarity_fingerprint) if record.similarity_fingerprint is not None else None
        with self._connection.transaction(), self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO corpus.documents (
                    document_id, source_name, document_type, title, url, published_at, content_hash,
                    processing_version, status, similarity_fingerprint, duplicate_of_document_id,
                    rejection_reason, failed_attempts, last_error_code
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id) DO UPDATE SET
                    source_name = EXCLUDED.source_name,
                    document_type = EXCLUDED.document_type,
                    title = EXCLUDED.title,
                    url = EXCLUDED.url,
                    published_at = EXCLUDED.published_at,
                    content_hash = EXCLUDED.content_hash,
                    processing_version = EXCLUDED.processing_version,
                    status = EXCLUDED.status,
                    similarity_fingerprint = EXCLUDED.similarity_fingerprint,
                    duplicate_of_document_id = EXCLUDED.duplicate_of_document_id,
                    rejection_reason = EXCLUDED.rejection_reason,
                    failed_attempts = EXCLUDED.failed_attempts,
                    last_error_code = EXCLUDED.last_error_code,
                    last_seen_at = now()
                """,
                (
                    record.document_id,
                    record.source_name,
                    record.document_type.value,
                    record.title,
                    record.url,
                    record.published_at,
                    record.content_hash,
                    record.processing_version,
                    record.status.value,
                    fingerprint,
                    record.duplicate_of_document_id,
                    record.rejection_reason.value if record.rejection_reason else None,
                    record.failed_attempts,
                    record.last_error_code.value if record.last_error_code else None,
                ),
            )
            cursor.execute("DELETE FROM corpus.parent_sections WHERE document_id = %s", (record.document_id,))
            cursor.executemany(
                "INSERT INTO corpus.parent_sections (parent_id, document_id, section, section_text) VALUES (%s, %s, %s, %s)",
                [
                    (f"{record.document_id}:{section.name}", record.document_id, section.name, section.text)
                    for section in parent_sections
                ],
            )

    def find_near_duplicates(self, fingerprint: int, max_distance: int, exclude_document_id: str) -> list[str]:
        """Active documents whose fingerprint differs by at most max_distance bits."""
        rows = self._connection.execute(
            """
            SELECT document_id FROM corpus.documents
            WHERE status = 'active'
              AND similarity_fingerprint IS NOT NULL
              AND document_id <> %s
              AND bit_count((similarity_fingerprint # %s)::bit(64)) <= %s
            """,
            (exclude_document_id, _to_signed(fingerprint), max_distance),
        ).fetchall()
        return [row[0] for row in rows]

    def mark_seen(self, document_ids: Sequence[str], seen_at: datetime) -> None:
        """Record that the source still lists these documents."""
        if not document_ids:
            return
        with self._connection.transaction():
            self._connection.execute(
                "UPDATE corpus.documents SET last_seen_at = %s WHERE document_id = ANY(%s)",
                (seen_at, list(document_ids)),
            )

    def record_failure(self, document_id: str, error_code: ErrorCode) -> int:
        """Count a failed attempt; returns the document's total failed attempts."""
        with self._connection.transaction():
            row = self._connection.execute(
                """
                UPDATE corpus.documents
                SET failed_attempts = failed_attempts + 1, last_error_code = %s
                WHERE document_id = %s
                RETURNING failed_attempts
                """,
                (error_code.value, document_id),
            ).fetchone()
        return row[0] if row else 0