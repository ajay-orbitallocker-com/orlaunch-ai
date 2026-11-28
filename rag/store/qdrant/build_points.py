"""Turns a chunk and its vectors into a Qdrant point """

from __future__ import annotations

import uuid

from qdrant_client import models

from rag.corpus.chunks import Chunk
from rag.store.qdrant.schema import DENSE_VECTOR, SPARSE_VECTOR

# Fixed namespace for point IDs; changing it gives every chunk a new ID, so never change it.
CHUNK_ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "orlaunch:corpus:chunk")


def point_id(chunk_id: str) -> str:
    """Stable Qdrant point ID for a chunk: the same chunk_id always gives the same UUID."""
    return str(uuid.uuid5(CHUNK_ID_NAMESPACE, chunk_id))

def point_metadata(chunk: Chunk) -> dict:
    
    """Fields stored on a chunk's point.
      indexed ones must match schema.METADATA_INDEXES."""
    
    document = chunk.document
    return {
        "document_id": document.document_id,
        "chunk_id": chunk.chunk_id,
        "chunk_hash": chunk.chunk_hash,
        "category": document.category.value,
        "document_type": document.document_type.value,
        "section": chunk.section,
        "source_name": document.source_name,
        "entities": list(document.entities),
        "parent_id": chunk.parent_id,
        "published_at": document.published_at.isoformat() if document.published_at else None,
        "title": document.title,
        "url": document.url,
        "text": chunk.text,
        "extra": dict(document.extra),   # type-specific fields, nested so they never clash with the ones above
    }

def build_point(chunk: Chunk, dense: list[float], sparse_indices: list[int], sparse_values: list[float]) -> models.PointStruct:
    """One Qdrant point: stable ID, both named vectors, and the chunk's metadata."""
    
    if not dense:
        raise ValueError(f"empty dense vector for {chunk.chunk_id}")
    
    if len(sparse_indices) != len(sparse_values):
        raise ValueError(f"sparse indices and values differ in length for {chunk.chunk_id}")
    
    return models.PointStruct(
        id=point_id(chunk.chunk_id),
        vector={
            DENSE_VECTOR: dense,
            SPARSE_VECTOR: models.SparseVector(indices=sparse_indices, values=sparse_values),
        },
        payload=point_metadata(chunk),
    )