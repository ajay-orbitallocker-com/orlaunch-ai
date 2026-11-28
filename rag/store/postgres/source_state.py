"""Sources, pauses and cursors, stored in the corpus schema in Postgres."""

from __future__ import annotations

from collections.abc import Sequence

import psycopg

from rag.ingestion.sources.definitions import SourceDefinition


class SourceState:
    """Implements SourceStateInterface; each write commits on its own."""

    def __init__(self, connection: psycopg.Connection) -> None:
        self._connection = connection   # opened by startup, closed by whoever opened it

    def sync_sources(self, definitions: Sequence[SourceDefinition]) -> None:
        """Write the declared sources into corpus.sources; run at startup."""
        rows = [
            (
                definition.source_name,
                definition.source_type.value,
                [document_type.value for document_type in definition.document_types],
                definition.trust_tier.value,
                definition.cadence.value,
                definition.terms_note,
            )
            for definition in definitions
        ]
        with self._connection.transaction(), self._connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO corpus.sources
                    (source_name, source_type, document_types, trust_tier, cadence, terms_note, synced_at)
                VALUES (%s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (source_name) DO UPDATE SET
                    source_type = EXCLUDED.source_type,
                    document_types = EXCLUDED.document_types,
                    trust_tier = EXCLUDED.trust_tier,
                    cadence = EXCLUDED.cadence,
                    terms_note = EXCLUDED.terms_note,
                    synced_at = now()
                """,
                rows,
            )

    def is_paused(self, source_name: str) -> bool:
        """True if the source has been paused; a paused source is not fetched."""
        row = self._connection.execute(
            "SELECT is_paused FROM corpus.source_controls WHERE source_name = %s",
            (source_name,),
        ).fetchone()
        return bool(row and row[0])

    def get_cursor(self, source_name: str) -> str | None:
        """Where the last successful run stopped; None on a source's first run."""
        row = self._connection.execute(
            "SELECT cursor_value FROM corpus.source_cursors WHERE source_name = %s",
            (source_name,),
        ).fetchone()
        return row[0] if row else None

    def save_cursor(self, source_name: str, cursor_value: str) -> None:
        """Move the cursor forward; call only after a run succeeds."""
        with self._connection.transaction():
            self._connection.execute(
                """
                INSERT INTO corpus.source_cursors (source_name, cursor_value, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (source_name) DO UPDATE SET
                    cursor_value = EXCLUDED.cursor_value,
                    updated_at = now()
                """,
                (source_name, cursor_value),
            )