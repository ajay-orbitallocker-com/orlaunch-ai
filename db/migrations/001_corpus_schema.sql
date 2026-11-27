-- 001: ingestion state for the search corpus, in its own "corpus" schema.
-- Definitions (categories, document types, sources) live in code; these tables
-- hold state and a copy of the source registry. Chunks live only in Qdrant.
-- No founder data belongs here.

CREATE SCHEMA IF NOT EXISTS corpus;

-- Copy of the source registry in code, rewritten at each ingestion startup.
-- Code is the source of truth; nothing here changes what is fetched or trusted.
CREATE TABLE corpus.sources (
    source_name    text PRIMARY KEY,                    -- e.g. nasa_techport
    kind           text NOT NULL CHECK (kind IN ('documents', 'facts', 'tool')),
    document_types text[] NOT NULL DEFAULT '{}',        -- document types it produces
    trust_tier     text NOT NULL CHECK (trust_tier IN ('primary', 'news')),
    cadence        text NOT NULL CHECK (cadence IN ('daily', 'weekly', 'monthly', 'on_demand')),
    terms_note     text NOT NULL DEFAULT '',            -- usage terms to respect
    synced_at      timestamptz NOT NULL DEFAULT now()   -- last copied from code
);

-- The only editable source setting: stop a source without a deploy.
-- It can only stop a source; it never changes where data comes from.
CREATE TABLE corpus.source_controls (
    source_name   text PRIMARY KEY REFERENCES corpus.sources (source_name) ON DELETE CASCADE,
    is_paused     boolean NOT NULL DEFAULT false,
    paused_reason text,
    paused_at     timestamptz,
    CHECK (is_paused = (paused_at IS NOT NULL))         -- a pause always has a time
);

-- Where each source's last successful fetch got to, for incremental runs.
-- Moved forward only after a run succeeds.
CREATE TABLE corpus.source_cursors (
    source_name  text PRIMARY KEY REFERENCES corpus.sources (source_name) ON DELETE CASCADE,
    cursor_value text NOT NULL,                         -- usually a date; the source's own format
    updated_at   timestamptz NOT NULL DEFAULT now()     -- when the last successful run finished
);

-- One row per document ever fetched: skip unchanged ones, catch duplicates,
-- remember rejections and repeated failures. Its chunks live in Qdrant,
-- found there by document_id.
CREATE TABLE corpus.documents (
    document_id              text PRIMARY KEY,          -- stable, e.g. techport:12345
    source_name              text NOT NULL REFERENCES corpus.sources (source_name),
    document_type            text NOT NULL,             -- validated in code against DocType
    title                    text NOT NULL,
    url                      text NOT NULL CHECK (url LIKE 'https://%'),
    published_at             timestamptz,
    content_hash             char(64) NOT NULL,         -- SHA-256 of normalised text
    processing_version       text NOT NULL,             -- chunking/processing that built its chunks
    similarity_fingerprint   bigint,                    -- near-duplicate fingerprint (SimHash)
    duplicate_of_document_id text REFERENCES corpus.documents (document_id),
    status                   text NOT NULL DEFAULT 'active' CHECK (status IN (
                                 'active', 'duplicate', 'superseded', 'removed',
                                 'rejected', 'quarantined')),
    rejection_reason         text CHECK (rejection_reason IN (
                                 'oversized', 'repetitive', 'injection_suspected',
                                 'missing_required_field', 'unsupported_format')),
    failed_attempts          integer NOT NULL DEFAULT 0 CHECK (failed_attempts >= 0),
    last_error_code          text CHECK (last_error_code IN (
                                 'fetch_failed', 'fetch_timeout', 'parse_failed',
                                 'embed_failed', 'write_failed')),
    first_seen_at            timestamptz NOT NULL DEFAULT now(),
    last_seen_at             timestamptz NOT NULL DEFAULT now(),
    CHECK ((status = 'duplicate') = (duplicate_of_document_id IS NOT NULL)),  -- a duplicate always names its original
    CHECK (duplicate_of_document_id IS DISTINCT FROM document_id),            -- never a duplicate of itself
    CHECK ((status = 'rejected') = (rejection_reason IS NOT NULL)),           -- a rejection always has a reason
    CHECK (status <> 'quarantined' OR last_error_code IS NOT NULL)            -- quarantine always has an error
);

CREATE INDEX documents_source_name_idx            ON corpus.documents (source_name);
CREATE INDEX documents_status_idx                 ON corpus.documents (status);
CREATE INDEX documents_similarity_fingerprint_idx ON corpus.documents (similarity_fingerprint)
    WHERE similarity_fingerprint IS NOT NULL;

-- Full sections, so retrieval can expand a small chunk into readable context.
CREATE TABLE corpus.parent_sections (
    parent_id    text PRIMARY KEY,                      -- <document_id>:<section>
    document_id  text NOT NULL REFERENCES corpus.documents (document_id) ON DELETE CASCADE,
    section      text NOT NULL,
    section_text text NOT NULL,
    UNIQUE (document_id, section)
);

-- What built each Qdrant version, and when it was live.
CREATE TABLE corpus.collection_versions (
    version_name        text PRIMARY KEY,               -- e.g. primary_sources_v1
    collection_name     text NOT NULL,                  -- e.g. primary_sources
    embedding_model     text NOT NULL,
    embedding_dimension integer NOT NULL CHECK (embedding_dimension > 0),
    created_at          timestamptz NOT NULL DEFAULT now(),
    went_live_at        timestamptz,
    retired_at          timestamptz,
    notes               text NOT NULL DEFAULT '',       -- what changed in this version
    CHECK (retired_at IS NULL OR went_live_at IS NOT NULL)  -- can't retire what never went live
);
