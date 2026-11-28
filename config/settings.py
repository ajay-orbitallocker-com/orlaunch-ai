"""Typed, validated settings loaded once at startup"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pydantic import SecretStr, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env sits at the repo root, found from this file's location, not the working folder.
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = REPO_ROOT / ".env"

# default output size per embedding model so that a configured dimension may not exceed it.
KNOWN_EMBEDDING_DIMENSIONS: dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}


class SettingsError(RuntimeError):
    """Settings are missing or invalid. The message never contains secret values."""


class Environment(str, Enum):
    """Where the process runs, staging and prod get stricter checks."""

    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"

class QdrantRole(str, Enum):
    """Which Qdrant key a process uses: the app reads, ingestion writes."""

    READ = "read"
    WRITE = "write"

def _settings_config(prefix: str, env_file: Path | None) -> SettingsConfigDict:
    """Shared config for one settings group reads only variables starting with prefix."""
    return SettingsConfigDict(
        env_prefix=prefix,           # field api_key + "OPENAI_" reads OPENAI_API_KEY
        env_file=env_file,           # .env path, or None for real environment variables only
        env_file_encoding="utf-8",   # read the file as UTF-8
        extra="ignore",              # skip other groups' variables in the shared .env
        case_sensitive=False,        # match names regardless of case, as Windows does
    )


class AppSettings(BaseSettings):
    """Process-wide settings, read from ORLAUNCH_* variables."""

    model_config = _settings_config("ORLAUNCH_", DEFAULT_ENV_FILE)

    env: Environment = Environment.DEV 


class OpenAISettings(BaseSettings):
    """OpenAI credentials, embedding model and request limits, read from OPENAI_* variables."""

    model_config = _settings_config("OPENAI_", DEFAULT_ENV_FILE)

    api_key: SecretStr                                # required hidden when printed
    org_id: str | None = None                         # optional organisation id
    project_id: str | None = None                     # optional project id
    embedding_model: str = "text-embedding-3-small"   # model used for all embeddings
    embedding_dimension: int = 1536                   # must match the Qdrant dense vector size
    timeout_seconds: float = 30.0                     # per-request timeout
    max_retries: int = 3                              # SDK retries with backoff on transient errors

    @field_validator("org_id", "project_id", mode="before")
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        """Treat an empty variable as not set."""
        return value or None

    @field_validator("timeout_seconds")
    @classmethod
    def _positive_timeout(cls, value: float) -> float:
        """Reject a zero or negative timeout."""
        if value <= 0:
            raise ValueError("must be greater than 0")
        return value

    @field_validator("max_retries")
    @classmethod
    def _non_negative_retries(cls, value: int) -> int:
        """Reject a negative retry count."""
        if value < 0:
            raise ValueError("must be 0 or more")
        return value

    @model_validator(mode="after")
    def _dimension_fits_model(self) -> "OpenAISettings":
        """Reject a dimension the configured model cannot produce."""
        native = KNOWN_EMBEDDING_DIMENSIONS.get(self.embedding_model)
        if self.embedding_dimension <= 0:
            raise ValueError("embedding_dimension must be greater than 0")
        if native is not None and self.embedding_dimension > native:
            raise ValueError(
                f"embedding_dimension {self.embedding_dimension} exceeds "
                f"{self.embedding_model}'s native size {native}"
            )
        return self

class QdrantSettings(BaseSettings):
    """Qdrant connection, role keys and collection aliases, read from QDRANT_* variables."""

    model_config = _settings_config("QDRANT_", DEFAULT_ENV_FILE)

    url: str = "http://localhost:6333"          # server URL; https outside dev
    read_api_key: SecretStr | None = None       # app key, read-only
    write_api_key: SecretStr | None = None      # ingestion key, read and write
    timeout_seconds: int = 10                   # per-request timeout
    prefer_grpc: bool = False                   # use gRPC instead of HTTP
    primary_sources_alias: str = "primary_sources"  # filings, rules, patents, TechPort
    news_sources_alias: str = "news_sources"        # news feeds, lower trust
    
    @model_validator(mode="after")
    def _aliases_distinct(self) -> "QdrantSettings":
        
        """Reject the same alias for both trust levels."""
        if self.primary_sources_alias == self.news_sources_alias:
            raise ValueError("primary_sources_alias and news_sources_alias must differ")        
        return self

    def api_key_for(self, role: QdrantRole) -> SecretStr | None:
        
        """The key matching the role never falls back to the other key."""
        return self.read_api_key if role is QdrantRole.READ else self.write_api_key

class PostgresSettings(BaseSettings):
    """Postgres connection, read from POSTGRES_* variables."""

    model_config = _settings_config("POSTGRES_", DEFAULT_ENV_FILE)

    dsn: SecretStr | None = None  # connection string -  required outside dev

@dataclass(frozen=True)
class Settings:
    """All settings for the process, grouped by concern."""

    app: AppSettings
    openai: OpenAISettings
    qdrant: QdrantSettings
    postgres: PostgresSettings

    @property
    def env(self) -> Environment:
        """Shortcut for settings.app.env."""
        return self.app.env

def _describe(error: ValidationError, group: str) -> str:
    
        """Field names and reasons only, never input values, which may be secrets."""
        
        parts = []
        for item in error.errors():
            location = ".".join(str(piece) for piece in item.get("loc", ())) or "(settings)"
            parts.append(f"{group}.{location}: {item.get('msg', 'invalid value')}")
        return "; ".join(parts)

def _require_for_deployed_env(settings: Settings) -> None:
        """Staging and prod must use TLS and real credentials."""
        if settings.env is Environment.DEV:
            return
        problems = []
        if not settings.qdrant.url.startswith("https://"):
            problems.append("QDRANT_URL must use https outside dev")
        if settings.qdrant.read_api_key is None:
            problems.append("QDRANT_READ_API_KEY is required outside dev")
        if settings.postgres.dsn is None:
            problems.append("POSTGRES_DSN is required outside dev")
        if problems:
            raise SettingsError("; ".join(problems))

def load_settings(env_file: Path | None = DEFAULT_ENV_FILE) -> Settings:
        """Read and validate all settings; call once, from app/wiring.py."""
        groups = (
            ("app", AppSettings),
            ("openai", OpenAISettings),
            ("qdrant", QdrantSettings),
            ("postgres", PostgresSettings),
        )
        loaded = {}
        for name, cls in groups:
            try:
                loaded[name] = cls(_env_file=env_file)  # env_file=None reads real variables only
            except ValidationError as error:
                raise SettingsError(_describe(error, name)) from None

        settings = Settings(**loaded)
        _require_for_deployed_env(settings)
        return settings

    