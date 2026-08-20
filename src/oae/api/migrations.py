"""Tracked PostgreSQL schema migrations for OAE production persistence."""

import argparse
from collections.abc import Iterable
from pathlib import Path

from oae.api.config import settings

MIGRATIONS_DIRECTORY = Path(__file__).parents[3] / "migrations" / "postgres"
MIGRATION_TABLE = "oae_schema_migrations"


def migration_files(directory: Path = MIGRATIONS_DIRECTORY) -> list[Path]:
    """Return the ordered, versioned PostgreSQL migration files."""
    return sorted(path for path in directory.glob("[0-9][0-9][0-9][0-9]_*.sql") if path.is_file())


def apply_postgres_migrations(connection, migrations: Iterable[Path] | None = None) -> list[str]:
    """Apply each unapplied migration in a transaction and return applied names."""
    pending = list(migrations) if migrations is not None else migration_files()
    applied: list[str] = []
    with connection.cursor() as cursor:
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} ("
            "name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now()"
            ")"
        )
        cursor.execute(f"SELECT name FROM {MIGRATION_TABLE}")
        completed = {row[0] for row in cursor.fetchall()}
        for migration in pending:
            if migration.name in completed:
                continue
            cursor.execute(migration.read_text(encoding="utf-8"))
            cursor.execute(f"INSERT INTO {MIGRATION_TABLE} (name) VALUES (%s)", (migration.name,))
            applied.append(migration.name)
    connection.commit()
    return applied


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply OAE PostgreSQL schema migrations.")
    parser.add_argument("--dry-run", action="store_true", help="Print pending migration names without applying them.")
    args = parser.parse_args()
    if settings.database_backend != "postgres":
        raise SystemExit("A PostgreSQL DATABASE_URL is required to apply OAE production migrations.")

    if args.dry_run:
        for migration in migration_files():
            print(migration.name)
        return 0

    import psycopg

    with psycopg.connect(settings.resolved_database_url) as connection:
        applied = apply_postgres_migrations(connection)
    print("No pending migrations." if not applied else f"Applied: {', '.join(applied)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
