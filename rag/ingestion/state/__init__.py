"""What ingestion remembers between runs: sources, pauses, cursors and document records; storage lives in rag.store.postgres."""

from rag.ingestion.state.ingestion_state_interface import DocumentStateInterface, SourceStateInterface

__all__ = ["DocumentStateInterface", "SourceStateInterface"]