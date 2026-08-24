import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Callable

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
    principal_id TEXT,
    principal_role TEXT,
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
CREATE TABLE IF NOT EXISTS repositories (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    provider TEXT NOT NULL CHECK (provider IN ('github')),
    external_id TEXT NOT NULL,
    clone_url TEXT NOT NULL,
    default_branch TEXT NOT NULL,
    credential_ref TEXT,
    status TEXT NOT NULL CHECK (status IN ('active', 'revoked', 'error')),
    last_synced_commit TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, provider, external_id)
);
CREATE TABLE IF NOT EXISTS repository_revisions (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    commit_sha TEXT NOT NULL,
    tree_sha TEXT,
    branch_name TEXT,
    manifest_sha256 TEXT,
    observed_at TEXT NOT NULL,
    UNIQUE (tenant_id, repository_id, commit_sha),
    FOREIGN KEY (tenant_id, repository_id)
        REFERENCES repositories (tenant_id, id)
);
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    repository_id TEXT NOT NULL,
    source_revision_id TEXT NOT NULL,
    parent_workspace_id TEXT,
    purpose TEXT NOT NULL CHECK (purpose IN ('source', 'execution', 'output', 'review')),
    state TEXT NOT NULL CHECK (state IN ('provisioning', 'ready', 'deleting', 'deleted', 'failed')),
    storage_uri TEXT NOT NULL,
    manifest_uri TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL DEFAULT 0 CHECK (size_bytes >= 0),
    file_count INTEGER NOT NULL DEFAULT 0 CHECK (file_count >= 0),
    retention_expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    ready_at TEXT,
    deleted_at TEXT,
    failure_code TEXT,
    failure_detail_redacted TEXT,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, repository_id) REFERENCES repositories (tenant_id, id),
    FOREIGN KEY (tenant_id, source_revision_id) REFERENCES repository_revisions (tenant_id, id)
);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_jobs_tenant_created ON jobs(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_repositories_tenant_active
    ON repositories (tenant_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_repository_revisions_tenant_repository
    ON repository_revisions (tenant_id, repository_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_workspaces_tenant_repository
    ON workspaces (tenant_id, repository_id, state, created_at DESC);
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
        principal_id TEXT,
        principal_role TEXT,
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

_POSTGRES_BOOTSTRAP_LOCK = threading.Lock()
_POSTGRES_BOOTSTRAPPED_URLS: set[str] = set()


class _ConnectionAdapter:
    """Small compatibility layer so existing repository code works on SQLite and Postgres."""

    def __init__(self, connection, backend: str, release: Callable[[Any], None] | None = None):
        self._connection = connection
        self.backend = backend
        self._release = release

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
        if self._release is not None:
            release, self._release = self._release, None
            release(self._connection)
        else:
            self._connection.close()


def _migrate_sqlite(adapter: _ConnectionAdapter) -> None:
    try:
        adapter.execute("ALTER TABLE api_keys ADD COLUMN key_prefix TEXT")
    except sqlite3.OperationalError:
        pass
    for statement in (
        "ALTER TABLE api_keys ADD COLUMN principal_id TEXT",
        "ALTER TABLE api_keys ADD COLUMN principal_role TEXT",
    ):
        try:
            adapter.execute(statement)
        except sqlite3.OperationalError:
            pass
    adapter.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix)")


def _connect() -> _ConnectionAdapter:
    backend = settings.database_backend
    if backend == "postgres":
        try:
            from oae.api.postgres_pool import _get_pool
        except ImportError as exc:
            raise RuntimeError("Postgres pool is not available") from exc
        pool = _get_pool()
        connection = pool.getconn(timeout=settings.postgres_pool_timeout_seconds)
        adapter = _ConnectionAdapter(connection, "postgres", release=pool.putconn)
        try:
            _bootstrap_postgres(adapter, settings.resolved_database_url)
        except Exception:
            adapter.close()
            raise
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


def _bootstrap_postgres(adapter: _ConnectionAdapter, database_url: str) -> None:
    """Create legacy base tables once per database URL without concurrent DDL deadlocks."""
    with _POSTGRES_BOOTSTRAP_LOCK:
        if database_url in _POSTGRES_BOOTSTRAPPED_URLS:
            return
        adapter.execute("SELECT pg_advisory_xact_lock(hashtextextended('oae:postgres-bootstrap', 0))")
        for statement in POSTGRES_STATEMENTS:
            adapter.execute(statement)
        adapter.execute("ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS key_prefix TEXT")
        adapter.execute("ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS principal_id TEXT")
        adapter.execute("ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS principal_role TEXT")
        adapter.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix)")
        adapter.commit()
        _POSTGRES_BOOTSTRAPPED_URLS.add(database_url)


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
