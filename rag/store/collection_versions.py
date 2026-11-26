"""
Versions of the corpus collections, and which version each one serves.

The code always reads a collection by its fixed name, e.g. "primary_sources".
The points live in numbered versions, e.g. "primary_sources_v1", and exactly
one version is live behind each fixed name at a time.

Version changes this module handles:
- First setup: create v1 and make it live.
- Upgrade: create the next version beside the live one, load and evaluate it,
  then make it live in one step. Needed only when the way data is processed or
  stored changes: a new embedding model, new chunking, a new metadata field to
  filter on, a metadata backfill for every chunk, new keyword (BM25)
  processing, different vector settings, or a rebuild after bad data.
- Rollback: make the previous version live again, in the same one step.

Not handled here, because they need no new version: daily and weekly
ingestion, and fixing or removing individual documents. Those update the live
version in place.

Changing versions needs the Qdrant write key. Qdrant calls the link from a
fixed name to a version an "alias"
"""

from __future__ import annotations

from qdrant_client import QdrantClient, models

from rag.store.schema import DENSE_VECTOR, SPARSE_VECTOR, CollectionSpec, SchemaMismatchError


def get_live_versions(client: QdrantClient) -> dict[str, str]:
    """Each fixed collection name mapped to the version it serves now."""
    return {item.alias_name: item.collection_name for item in client.get_aliases().aliases}


def create_empty_version(client: QdrantClient, spec: CollectionSpec, version: str) -> str:
    """Create an empty, not-yet-live version with both vectors and every metadata index."""
    target = spec.version_name(version)
    if client.collection_exists(target):
        raise SchemaMismatchError(f"version '{target}' already exists; choose a new version")

    client.create_collection(
        collection_name=target,
        vectors_config={DENSE_VECTOR: models.VectorParams(size=spec.dense_size, distance=spec.distance)},
        sparse_vectors_config={SPARSE_VECTOR: models.SparseVectorParams(modifier=models.Modifier.IDF)},
    )
    for field_name, schema in spec.metadata_indexes.items():
        client.create_payload_index(collection_name=target, field_name=field_name, field_schema=schema, wait=True)
    return target


def set_live_version(client: QdrantClient, spec: CollectionSpec, version: str) -> str:
    """
    Switch which version spec.name serves, e.g. primary_sources to primary_sources_v2.

    Used for first setup, upgrades and rollbacks. The switch is sent as one
    request, so searches never find the name missing.

    Returns the name of the version now live.
    Raises SchemaMismatchError if that version hasn't been created yet.
    """
    new_version = spec.version_name(version)
    if not client.collection_exists(new_version):
        raise SchemaMismatchError(f"version '{new_version}' does not exist; create it first")

    already_serving = spec.name in get_live_versions(client)

    instructions = []
    if already_serving:
        instructions.append(_stop_serving(spec.name))
    instructions.append(_start_serving(spec.name, new_version))

    client.update_collection_aliases(change_aliases_operations=instructions)
    return new_version


def _stop_serving(name: str) -> models.DeleteAliasOperation:
    """Instruction for Qdrant: name stops serving its current version."""
    return models.DeleteAliasOperation(delete_alias=models.DeleteAlias(alias_name=name))


def _start_serving(name: str, version_name: str) -> models.CreateAliasOperation:
    """Instruction for Qdrant: name starts serving version_name."""
    return models.CreateAliasOperation(create_alias=models.CreateAlias(alias_name=name, collection_name=version_name))