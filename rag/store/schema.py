"""Qdrant schema for the search corpus -  collections, named vectors and metadata indexes, as data."""

from __future__ import annotations

from dataclasses import dataclass, field

from qdrant_client import QdrantClient, models

DENSE_VECTOR = "dense"  # OpenAI embedding, searched with HNSW
SPARSE_VECTOR = "bm25"  # BM25 term weights, keyword search

# Metadata fields retrieval filters on 
# add new ones before the ingestion that needs them.
METADATA_INDEXES: dict[str, models.PayloadSchemaType] = {
    "category": models.PayloadSchemaType.KEYWORD,
    "document_type": models.PayloadSchemaType.KEYWORD,
    "section": models.PayloadSchemaType.KEYWORD,
    "source_name": models.PayloadSchemaType.KEYWORD,
    "entities": models.PayloadSchemaType.KEYWORD,
    "document_id": models.PayloadSchemaType.KEYWORD,   # find and clean up a document's chunks
    "parent_id": models.PayloadSchemaType.KEYWORD,
    "extra.cpc_codes": models.PayloadSchemaType.KEYWORD,     # patents only
    "extra.cfr_section": models.PayloadSchemaType.KEYWORD,   # regulations only
    "published_at": models.PayloadSchemaType.DATETIME,
}


class SchemaMismatchError(RuntimeError):
    """A collection doesn't match the declared schema; fix by rebuilding, not patching."""


@dataclass(frozen=True)
class CollectionSpec:
    """One collection the code reads by a fixed name, stored as numbered versions."""

    name: str                                               # fixed name the code uses, e.g. primary_sources
    dense_size: int                                         # must equal the embedding dimension
    distance: models.Distance = models.Distance.COSINE      # OpenAI embeddings use cosine
    metadata_indexes: dict[str, models.PayloadSchemaType] = field(
        default_factory=lambda: dict(METADATA_INDEXES)
    )

    def version_name(self, version: str) -> str:
        """Where a version's points are stored, e.g. primary_sources_v1."""
        return f"{self.name}_{version}"


def build_collection_specs(primary_sources_collection: str, news_sources_collection: str, dense_size: int) -> list[CollectionSpec]:
    """Two collections by trust level: primary sources, and news sources."""
    return [
        CollectionSpec(name=primary_sources_collection, dense_size=dense_size),
        CollectionSpec(name=news_sources_collection, dense_size=dense_size),
    ]