"""Client factories: build OpenAI and Qdrant clients from settings, only when called."""

from __future__ import annotations
import psycopg

from openai import OpenAI
from qdrant_client import QdrantClient

from config.settings import Environment, OpenAISettings, QdrantRole, QdrantSettings, SettingsError,PostgresSettings

def build_open_ai_client(settings : OpenAISettings) -> OpenAI:
     
    """OpenAI client with a bounded timeout and the SDK's retry with backoff."""
    return OpenAI(
        api_key = settings.api_key.get_secret_value(), # unwrap the secret only here
        organization=settings.org_id,
        project = settings.project_id,
        timeout = settings.timeout_seconds,
        max_retries=settings.max_retries,
        )

def build_qdrant_client( settings: QdrantSettings, role: QdrantRole, env: Environment = Environment.DEV,) -> QdrantClient:
    """Qdrant client for one role, outside dev a key for that role is required."""
    
    key = settings.api_key_for(role)
    if key is None and env is not Environment.DEV:
        raise SettingsError(f"no Qdrant API key configured for role '{role.value}' in {env.value}")

    return QdrantClient(
        url=settings.url,
        api_key=key.get_secret_value() if key is not None else None,  # None allowed in dev only
        timeout=settings.timeout_seconds,
        prefer_grpc=settings.prefer_grpc,
    )

def build_postgres_connection(settings: PostgresSettings) -> psycopg.Connection:
    """Postgres connection from POSTGRES_DSN, with a bounded connect timeout."""
    if settings.dsn is None:
        raise SettingsError("POSTGRES_DSN is not set")
    return psycopg.connect(settings.dsn.get_secret_value(), connect_timeout=10)