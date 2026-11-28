-- 002: name the source column to match SourceType in code.
ALTER TABLE corpus.sources RENAME COLUMN kind TO source_type;