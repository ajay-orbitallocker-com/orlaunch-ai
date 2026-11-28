"""One-off check of the state layer against your database; run once, then delete this file."""

from config.settings import load_settings
from infra.clients import build_postgres_connection
from rag.corpus.categories import TrustTier
from rag.corpus.document_types import DocumentType
from rag.corpus.documents import Section
from rag.ingestion.sources.definitions import Cadence, SourceDefinition, SourceType
from rag.ingestion.state.document_records import DocumentRecord, DocumentStatus, ErrorCode
from rag.store.postgres.document_state import DocumentState
from rag.store.postgres.source_state import SourceState

connection = build_postgres_connection(load_settings().postgres)
sources, documents = SourceState(connection), DocumentState(connection)
largest = (1 << 64) - 1   # the fingerprint that needs the signed conversion
try:
    sources.sync_sources([SourceDefinition("check_source", SourceType.DOCUMENTS, (DocumentType.TECHPORT_PROJECT,), TrustTier.PRIMARY, Cadence.WEEKLY)])
    record = DocumentRecord("check:1", "check_source", DocumentType.TECHPORT_PROJECT, "t", "https://x", None, "a" * 64, "v1", DocumentStatus.ACTIVE, similarity_fingerprint=largest)
    documents.save_document(record, [Section(name="description", text="x")])
    sources.save_cursor("check_source", "2026-11-01")
    stored = documents.get_documents(["check:1"])["check:1"]
    print(stored.similarity_fingerprint == largest, sources.get_cursor("check_source"), sources.is_paused("check_source"), documents.record_failure("check:1", ErrorCode.FETCH_FAILED))
finally:
    with connection.transaction():
        connection.execute("DELETE FROM corpus.documents WHERE source_name = 'check_source'")
        connection.execute("DELETE FROM corpus.sources WHERE source_name = 'check_source'")
    connection.close()