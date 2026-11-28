"""
Health of the corpus collections: find problems and report them, never stop anything.

Used in two ways:
- setup_collections.py calls find_collection_problems and raises if any are
  found, so startup and ingestion stop on a broken collection.
- A scheduled job in the app layer calls check_collection_health and
  find_version_changes, then records the results as logs, metrics or alerts.
  That job decides how to record them; this module only returns plain results.

What counts as a problem:
- no live version behind a collection's fixed name
- dense vector missing, or a different size or distance than the schema
- BM25 vector missing
- a metadata field the schema indexes but the live version doesn't

Results hold only collection names, version names and problem descriptions,
never founder text, so they are safe to log.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from qdrant_client import QdrantClient

from rag.store.qdrant.collection_versions import get_live_versions
from rag.store.qdrant.schema import DENSE_VECTOR, SPARSE_VECTOR, CollectionSpec


@dataclass(frozen=True)
class CollectionHealth:
    """Health of one collection at the moment it was checked."""

    name: str                                           # fixed name, e.g. primary_sources
    live_version: str | None                            # e.g. primary_sources_v1; None if nothing is live
    problems: list[str] = field(default_factory=list)   # empty when healthy

    @property
    def healthy(self) -> bool:
        """True when no problems were found."""
        return not self.problems


@dataclass(frozen=True)
class VersionChange:
    """A collection that started serving a different version between two checks."""

    name: str
    previous_version: str | None   # None if it had no live version before
    current_version: str | None    # None if it has no live version now


def find_collection_problems(
    client: QdrantClient,
    spec: CollectionSpec,
    require_metadata_indexes: bool = True,
) -> CollectionHealth:
    """
    Check the live version behind spec.name against the schema; never raises.

    require_metadata_indexes=False is only for in-memory Qdrant in unit tests,
    which ignores metadata indexes; never turn it off against a real server.
    """
    live_version = get_live_versions(client).get(spec.name)
    if live_version is None:
        return CollectionHealth(name=spec.name, live_version=None, problems=["no live version"])

    config = client.get_collection(live_version)
    problems = _vector_problems(config, spec)
    if require_metadata_indexes:
        problems += _metadata_index_problems(config, spec)

    return CollectionHealth(name=spec.name, live_version=live_version, problems=problems)


def check_collection_health(
    client: QdrantClient,
    specs: list[CollectionSpec],
    require_metadata_indexes: bool = True,
) -> list[CollectionHealth]:
    """Health of every collection, for a scheduled check; never raises."""
    return [find_collection_problems(client, spec, require_metadata_indexes) for spec in specs]


def find_version_changes(previous: dict[str, str], current: dict[str, str]) -> list[VersionChange]:
    """
    Collections serving a different version now than in the previous snapshot.

    Both arguments come from get_live_versions(). A change during a planned
    upgrade or rollback is expected; any other change is worth an alert.
    """
    names = sorted(set(previous) | set(current))
    return [
        VersionChange(name=name, previous_version=previous.get(name), current_version=current.get(name))
        for name in names
        if previous.get(name) != current.get(name)
    ]


def _vector_problems(config, spec: CollectionSpec) -> list[str]:
    """Differences between the live version's vectors and the schema."""
    problems = []

    dense_vectors = config.config.params.vectors
    dense = dense_vectors.get(DENSE_VECTOR) if isinstance(dense_vectors, dict) else None
    if dense is None:
        problems.append(f"missing dense vector '{DENSE_VECTOR}'")
    else:
        if dense.size != spec.dense_size:
            problems.append(f"dense size is {dense.size}, expected {spec.dense_size}")
        if dense.distance != spec.distance:
            problems.append(f"dense distance is {dense.distance}, expected {spec.distance}")

    sparse_vectors = config.config.params.sparse_vectors or {}
    if SPARSE_VECTOR not in sparse_vectors:
        problems.append(f"missing sparse vector '{SPARSE_VECTOR}'")

    return problems


def _metadata_index_problems(config, spec: CollectionSpec) -> list[str]:
    """Metadata fields the schema indexes but the live version doesn't."""
    indexed_fields = set((config.payload_schema or {}).keys())  # Qdrant calls metadata "payload"
    missing = sorted(set(spec.metadata_indexes) - indexed_fields)
    if not missing:
        return []
    return [f"missing metadata indexes {missing} (needs a new version for filter-aware search)"]