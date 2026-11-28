"""
Apply database migrations: the numbered .sql files in db/migrations, in order, once each.

Each file runs in its own transaction, so a failing file leaves no half-made
tables. Applied files are recorded in public.schema_migrations with a checksum;
editing a file after it has been applied is an error, because the database
would no longer match the file. To change a table, add a new numbered file.

Run from orlaunch-ai/:  python -m db.migrate
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import psycopg

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"

_CREATE_LEDGER = """
CREATE TABLE IF NOT EXISTS public.schema_migrations (
    filename   text PRIMARY KEY,
    checksum   char(64) NOT NULL,
    applied_at timestamptz NOT NULL DEFAULT now()
)
"""


class MigrationError(RuntimeError):
    """A migration was edited after being applied, or failed to apply."""


def migration_files(directory: Path = MIGRATIONS_DIR) -> list[Path]:
    """Migration files in the order they apply: 001_..., 002_..., and so on."""
    return sorted(directory.glob("[0-9][0-9][0-9]_*.sql"))


def apply_migrations(connection: psycopg.Connection, directory: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply every migration not yet applied; returns the names of those applied now."""
    with connection.transaction():
        connection.execute(_CREATE_LEDGER)
    applied = _applied_checksums(connection)

    newly_applied = []
    for path in migration_files(directory):
        checksum = _checksum(path)
        recorded = applied.get(path.name)

        if recorded is not None:
            if recorded != checksum:
                raise MigrationError(f"{path.name} was edited after it was applied; add a new migration instead")
            continue

        try:
            with connection.transaction():
                connection.execute(path.read_text(encoding="utf-8"))
                connection.execute(
                    "INSERT INTO public.schema_migrations (filename, checksum) VALUES (%s, %s)",
                    (path.name, checksum),
                )
        except psycopg.Error as error:
            raise MigrationError(f"{path.name} failed: {error.__class__.__name__}") from None
        newly_applied.append(path.name)
    return newly_applied


def _applied_checksums(connection: psycopg.Connection) -> dict[str, str]:
    """Filename to checksum for every migration already applied."""
    rows = connection.execute("SELECT filename, checksum FROM public.schema_migrations").fetchall()
    return {filename: checksum for filename, checksum in rows}


def _checksum(path: Path) -> str:
    """SHA-256 of the file, to detect edits after applying."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    """Apply pending migrations to the database in POSTGRES_DSN."""
    from config.settings import load_settings
    from infra.clients import build_postgres_connection

    settings = load_settings()
    with build_postgres_connection(settings.postgres) as connection:
        newly_applied = apply_migrations(connection)
    print("applied:", newly_applied or "nothing new")


if __name__ == "__main__":
    main()
