"""
Set up and check the corpus collections and stop when something is wrong.

Two jobs, for two kinds of process:

- check_collection: read-only. The app runs it at startup with the read key,
  so a collection that doesn't match the schema stops deployment instead of
  breaking searches later.
- setup_collections: run by ingestion jobs with the write key. On the very
  first run, when a collection has no live version, it creates v1 and makes it
  live. On every later run it only checks; it never patches a live version.
  A mismatch means a rebuild: create the next version and make it live.

The checks themselves live in collection_health.py, which reports problems
without stopping anything; this module turns any problem into an error.
"""

from __future__ import annotations

from qdrant_client import QdrantClient

from rag.store.collection_health import find_collection_problems
from rag.store.collection_versions import create_empty_version, get_live_versions, set_live_version
from rag.store.schema import CollectionSpec, SchemaMismatchError


def check_collection(client: QdrantClient, spec: CollectionSpec, require_metadata_indexes: bool = True) -> None:
    """
    Raise SchemaMismatchError if the live version behind spec.name doesn't match the schema.

    require_metadata_indexes=False is only for in-memory Qdrant in unit tests,
    which ignores metadata indexes; never turn it off against a real server.
    """
    health = find_collection_problems(client, spec, require_metadata_indexes)
    if health.healthy:
        return
    if health.live_version is None:
        raise SchemaMismatchError(f"'{spec.name}' has no live version; run setup_collections first")
    raise SchemaMismatchError(f"'{spec.name}' (live version '{health.live_version}'): " + "; ".join(health.problems))


def setup_collections(
    client: QdrantClient,
    specs: list[CollectionSpec],
    first_version: str = "v1",
    require_metadata_indexes: bool = True,
) -> list[str]:
    """
    Make sure every collection has a live version that matches the schema.

    A collection with no live version gets first_version created and made live.
    A collection that already has one is only checked.
    Returns a note for each version created; an empty list means nothing changed.
    """
    notes = []
    for spec in specs:
        has_live_version = spec.name in get_live_versions(client)

        if has_live_version:
            check_collection(client, spec, require_metadata_indexes)
            continue

        create_empty_version(client, spec, first_version)
        live_version = set_live_version(client, spec, first_version)
        notes.append(f"created '{live_version}' and made it live as '{spec.name}'")
    return notes