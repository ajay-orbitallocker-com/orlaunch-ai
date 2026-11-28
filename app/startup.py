"""
What each process builds at startup: the one place that reads settings and creates clients.

Two kinds of process get different access from the same code:
- build_app_services(): the backend API and CDD workers. Read-only Qdrant key;
  checks both collections at startup and refuses to start if either is wrong.
- build_ingestion_services(): scheduled ingestion jobs and admin commands.
  Write key; creates any collection that has no live version, checks the rest.  

"""

from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI
from qdrant_client import QdrantClient

from config.settings import QdrantRole, Settings, load_settings
from infra.clients import build_openai_client, build_qdrant_client
from rag.store.qdrant.schema import CollectionSpec, build_collection_specs
from rag.store.qdrant.setup_collections import check_collection, setup_collections


@dataclass(frozen=True)
class CorpusCollections:
    """The two corpus collections, by fixed name."""

    primary_sources: CollectionSpec   # filings, rules, patents, TechPort
    news_sources: CollectionSpec      # news feeds, lower trust

    @property
    def all(self) -> list[CollectionSpec]:
        """Both collections, primary sources first."""
        return [self.primary_sources, self.news_sources]


@dataclass(frozen=True)
class Services:
    """Everything a process needs, built once at startup."""

    settings: Settings
    role: QdrantRole          # READ for the app, WRITE for ingestion
    openai: OpenAI
    qdrant: QdrantClient
    collections: CorpusCollections


def build_app_services(settings: Settings | None = None, check_schema: bool = True) -> Services:
    """
    Services for the backend API and CDD workers -  read-only access to the corpus.

    Raises SchemaMismatchError at startup if either collection doesn't match
    the schema. check_schema=False is only for tests with fake clients.
    """
    services = _build(settings or load_settings(), QdrantRole.READ)
    if check_schema:
        for spec in services.collections.all:
            check_collection(services.qdrant, spec)
    return services


def build_ingestion_services(settings: Settings | None = None, first_version: str = "v1") -> tuple[Services, list[str]]:
    """
    Services for ingestion jobs and admin commands -  write access to the corpus.

    Creates and makes live any collection with no live version, and checks the
    rest. Returns the services and a note for each version created.
    """
    services = _build(settings or load_settings(), QdrantRole.WRITE)
    notes = setup_collections(services.qdrant, services.collections.all, first_version=first_version)
    return services, notes


def _build(settings: Settings, role: QdrantRole) -> Services:
    """Clients and collection specs for one role."""
    return Services(
        settings=settings,
        role=role,
        openai=build_openai_client(settings.openai),
        qdrant=build_qdrant_client(settings.qdrant, role, settings.env),
        collections=_corpus_collections(settings),
    )


def _corpus_collections(settings: Settings) -> CorpusCollections:
    """Collection specs from settings, sized to the configured embedding model."""
    primary_sources, news_sources = build_collection_specs(
        primary_sources_collection=settings.qdrant.primary_sources_collection,
        news_sources_collection=settings.qdrant.news_sources_collection,
        dense_size=settings.openai.embedding_dimension,
    )
    return CorpusCollections(primary_sources=primary_sources, news_sources=news_sources)