import sqlite3
from contextlib import contextmanager
from typing import Any

from oae.api.config import settings

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    key_prefix TEXT,
    key_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    revoked_at TEXT
);
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    status TEXT NOT NULL,
    operation TEXT NOT NULL,
    payload TEXT NOT NULL,
    result TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_jobs_tenant_created ON jobs(tenant_id, created_at DESC);
"""

POSTGRES_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS tenants (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS api_keys (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL REFERENCES tenants(id),
        key_prefix TEXT,
        key_hash TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL,
        revoked_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL REFERENCES tenants(id),
        status TEXT NOT NULL,
        operation TEXT NOT NULL,
        payload TEXT NOT NULL,
        result TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix)",
    "CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash)",
    "CREATE INDEX IF NOT EXISTS idx_jobs_tenant_created ON jobs(tenant_id, created_at DESC)",
)


class _ConnectionAdapter:
    """Small compatibility layer so existing repository code works on SQLite and Postgres."""

    def __init__(self, connection, backend: str):
        self._connection = connection
        self.backend = backend

    def execute(self, query: str, params=()):
        if self.backend == "postgres":
            query = query.replace("?", "%s")
        return self._connection.execute(query, params)

    def executescript(self, script: str):
        if self.backend != "sqlite":
            raise RuntimeError("executescript is only available for SQLite")
        return self._connection.executescript(script)

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()


def _migrate_sqlite(adapter: _ConnectionAdapter) -> None:
    try:
        adapter.execute("ALTER TABLE api_keys ADD COLUMN key_prefix TEXT")
    except sqlite3.OperationalError:
        pass
    adapter.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix)")


def _connect() -> _ConnectionAdapter:
    backend = settings.database_backend
    if backend == "postgres":
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("Postgres is configured but psycopg is not installed") from exc
        connection: Any = psycopg.connect(settings.resolved_database_url)
        adapter = _ConnectionAdapter(connection, "postgres")
        for statement in POSTGRES_STATEMENTS:
            adapter.execute(statement)
        adapter.execute("ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS key_prefix TEXT")
        adapter.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix)")
        return adapter

    if backend == "sqlite":
        path = settings.sqlite_path
        if path.parent != path.parent.parent:
            path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        adapter = _ConnectionAdapter(connection, "sqlite")
        adapter.executescript(SQLITE_SCHEMA)
        _migrate_sqlite(adapter)
        return adapter

    raise RuntimeError(
        "No supported persistent database configured. Set DATABASE_URL or POSTGRES_URL."
    )


@contextmanager
def db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
