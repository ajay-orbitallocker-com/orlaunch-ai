"""Qdrant schema for the search corpus- collections, named vectors and payload indexes, as data."""

from __future__ import annotations

from dataclasses import dataclass, field

from qdrant_client import QdrantClient, models

DENSE_VECTOR = "dense"  # OpenAI embedding, searched with HNSW
SPARSE_VECTOR = "bm25"  # BM25 term weights, keyword search

# Fields retrieval filters on, add new ones here before the ingestion that needs them.

PAYLOAD_INDEXES: dict[str, models.PayloadSchemaType] = {
    "category": models.PayloadSchemaType.KEYWORD,
    "doc_type": models.PayloadSchemaType.KEYWORD,
    "section": models.PayloadSchemaType.KEYWORD,       # keeps TechPort boilerplate out of market answers
    "source": models.PayloadSchemaType.KEYWORD,
    "entities": models.PayloadSchemaType.KEYWORD,      # company and program names for competitor queries
    "parent_id": models.PayloadSchemaType.KEYWORD,
    "cpc_codes": models.PayloadSchemaType.KEYWORD,     # patent classes
    "cfr_section": models.PayloadSchemaType.KEYWORD,   # regulation sections
    "published_at": models.PayloadSchemaType.DATETIME,
}

class SchemaMismatchError(RuntimeError):
    """A collection doesn't match the declared schema - fix by rebuilding, not patching."""

@dataclass(frozen=True)
class CollectionSpec:
    """What one aliased collection must look like."""

    alias: str                                              # name the code reads through
    dense_size: int                                         # must equal the embedding dimension
    distance: models.Distance = models.Distance.COSINE      # OpenAI embeddings use cosine
    payload_indexes: dict[str, models.PayloadSchemaType] = field(
        default_factory=lambda: dict(PAYLOAD_INDEXES)       # a fresh copy per spec
    )

    def physical_name(self, version: str) -> str:
        """The real collection behind the alias, e.g. corpus_primary_v1."""
        return f"{self.alias}_{version}"

def build_collection_specs(primary_sources_alias: str, news_sources_alias: str, dense_size: int) -> list[CollectionSpec]:
    
    """Two collections by trust level: primary sources, and news sources."""
    return [
        CollectionSpec(alias=primary_sources_alias, dense_size=dense_size),
        CollectionSpec(alias=news_sources_alias, dense_size=dense_size),
    ]
def _alias_targets(client: QdrantClient) -> dict[str, str]:
    
    """Map of alias name to the collection it points at."""
    return {item.alias_name: item.collection_name for item in client.get_aliases().aliases}

def create_versioned_collection(client: QdrantClient, spec: CollectionSpec, version: str) -> str:
    
    """Create <alias>_<version> with both vectors and every payload index, alias untouched."""
    name = spec.physical_name(version)
    
    if client.collection_exists(name):
        raise SchemaMismatchError(f"collection '{name}' already exists. Choose a new version")

    #create a new collection
    client.create_collection(
        collection_name=name,
        #for embeddings
        vectors_config={DENSE_VECTOR: models.VectorParams(size=spec.dense_size, distance=spec.distance)},
         # BM25 rarity weighting
        sparse_vectors_config={SPARSE_VECTOR: models.SparseVectorParams(modifier=models.Modifier.IDF)}, 
    )
    for field_name, schema in spec.payload_indexes.items():
        client.create_payload_index(collection_name=name, field_name=field_name, field_schema=schema, wait=True)  # before any points
    return name