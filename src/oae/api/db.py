import sqlite3
import threading
from contextlib import contextmanager
from contextvars import ContextVar
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
    authorization_id TEXT,
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
CREATE TABLE IF NOT EXISTS rate_limit_buckets (
    scope TEXT NOT NULL,
    subject TEXT NOT NULL,
    window_start BIGINT NOT NULL,
    hit_count INTEGER NOT NULL CHECK (hit_count >= 0),
    PRIMARY KEY (scope, subject, window_start)
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
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
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
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        deleted_at TIMESTAMPTZ,
        UNIQUE (tenant_id, id),
        UNIQUE (tenant_id, provider, external_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS repository_revisions (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        repository_id TEXT NOT NULL,
        commit_sha TEXT NOT NULL,
        tree_sha TEXT,
        branch_name TEXT,
        manifest_sha256 TEXT,
        observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (tenant_id, id),
        UNIQUE (tenant_id, repository_id, commit_sha),
        FOREIGN KEY (tenant_id, repository_id) REFERENCES repositories (tenant_id, id)
    )
    """,
    """
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
        size_bytes BIGINT NOT NULL DEFAULT 0 CHECK (size_bytes >= 0),
        file_count INTEGER NOT NULL DEFAULT 0 CHECK (file_count >= 0),
        retention_expires_at TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        ready_at TIMESTAMPTZ,
        deleted_at TIMESTAMPTZ,
        failure_code TEXT,
        failure_detail_redacted TEXT,
        UNIQUE (tenant_id, id),
        FOREIGN KEY (tenant_id, repository_id) REFERENCES repositories (tenant_id, id),
        FOREIGN KEY (tenant_id, source_revision_id) REFERENCES repository_revisions (tenant_id, id),
        FOREIGN KEY (tenant_id, parent_workspace_id) REFERENCES workspaces (tenant_id, id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS workspace_manifest_entries (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL REFERENCES tenants(id),
        workspace_id TEXT NOT NULL,
        relative_path TEXT NOT NULL,
        object_key TEXT NOT NULL,
        sha256 TEXT NOT NULL CHECK (sha256 ~ '^[a-f0-9]{64}$'),
        size_bytes BIGINT NOT NULL CHECK (size_bytes >= 0),
        content_type TEXT NOT NULL,
        is_executable BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (tenant_id, workspace_id, relative_path),
        FOREIGN KEY (tenant_id, workspace_id) REFERENCES workspaces (tenant_id, id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rate_limit_buckets (
        scope TEXT NOT NULL,
        subject TEXT NOT NULL,
        window_start BIGINT NOT NULL,
        hit_count INTEGER NOT NULL CHECK (hit_count >= 0),
        PRIMARY KEY (scope, subject, window_start)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix)",
    "CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash)",
    "CREATE INDEX IF NOT EXISTS idx_jobs_tenant_created ON jobs(tenant_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_repositories_tenant_active ON repositories (tenant_id, status, created_at DESC) WHERE deleted_at IS NULL",
    "CREATE INDEX IF NOT EXISTS idx_repository_revisions_tenant_repository ON repository_revisions (tenant_id, repository_id, observed_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_workspace_expiry ON workspaces (tenant_id, retention_expires_at) WHERE state IN ('ready', 'failed')",
    "CREATE INDEX IF NOT EXISTS idx_workspace_repository_state ON workspaces (tenant_id, repository_id, state, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_workspace_manifest_listing ON workspace_manifest_entries (tenant_id, workspace_id, relative_path)",
)

_POSTGRES_BOOTSTRAP_LOCK = threading.Lock()
_POSTGRES_BOOTSTRAPPED_URLS: set[str] = set()
_WORKER_DATABASE_CONTEXT: ContextVar[bool] = ContextVar("oae_worker_database", default=False)


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
    for statement in (
        "ALTER TABLE api_keys ADD COLUMN principal_id TEXT",
        "ALTER TABLE api_keys ADD COLUMN principal_role TEXT",
    ):
        try:
            adapter.execute(statement)
        except sqlite3.OperationalError:
            pass
    adapter.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix)")
    try:
        adapter.execute("ALTER TABLE jobs ADD COLUMN authorization_id TEXT")
    except sqlite3.OperationalError:
        pass
    adapter.execute("""CREATE TABLE IF NOT EXISTS engineering_change_sets (
        id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, workspace_id TEXT NOT NULL,
        repository_id TEXT NOT NULL, source_revision_id TEXT NOT NULL,
        local_commit_sha TEXT NOT NULL, remote_commit_sha TEXT, branch_name TEXT NOT NULL,
        status TEXT NOT NULL, pr_number INTEGER, pr_url TEXT, title TEXT, summary TEXT,
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
        UNIQUE (tenant_id, id)
    )""")
    adapter.execute("""CREATE TABLE IF NOT EXISTS engineering_change_files (
        id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, change_set_id TEXT NOT NULL,
        path TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
        UNIQUE (tenant_id, change_set_id, path)
    )""")
    adapter.execute("CREATE INDEX IF NOT EXISTS idx_change_sets_tenant_created ON engineering_change_sets(tenant_id, created_at DESC)")
    adapter.execute("CREATE INDEX IF NOT EXISTS idx_change_files_set ON engineering_change_files(tenant_id, change_set_id)")


@contextmanager
def worker_database_context():
    token = _WORKER_DATABASE_CONTEXT.set(True)
    try:
        yield
    finally:
        _WORKER_DATABASE_CONTEXT.reset(token)


def _connect(tenant_id: str | None = None) -> _ConnectionAdapter:
    backend = settings.database_backend
    worker_context = _WORKER_DATABASE_CONTEXT.get()
    database_url = (
        settings.resolved_worker_database_url
        if worker_context
        else settings.resolved_database_url
    )
    if backend == "postgres":
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("Postgres is configured but psycopg is not installed") from exc
        if not database_url:
            raise RuntimeError("PostgreSQL database URL is not configured for this runtime")
        connection: Any = psycopg.connect(database_url)
        adapter = _ConnectionAdapter(connection, "postgres")
        if not worker_context:
            _bootstrap_postgres(adapter, database_url)
        if tenant_id:
            adapter.execute("SELECT set_config('oae.tenant_id', ?, true)", (tenant_id,))
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
    """Create legacy base tables once per connection URL without concurrent DDL deadlocks."""
    with _POSTGRES_BOOTSTRAP_LOCK:
        if database_url in _POSTGRES_BOOTSTRAPPED_URLS:
            return
        adapter.execute("SELECT pg_advisory_xact_lock(hashtextextended('oae:postgres-bootstrap', 0))")
        for statement in POSTGRES_STATEMENTS:
            adapter.execute(statement)
        adapter.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS result TEXT")
        adapter.execute("ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS key_prefix TEXT")
        adapter.execute("ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS principal_id TEXT")
        adapter.execute("ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS principal_role TEXT")
        adapter.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix)")
        adapter.execute("""CREATE TABLE IF NOT EXISTS engineering_change_sets (
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, workspace_id TEXT NOT NULL,
            repository_id TEXT NOT NULL, source_revision_id TEXT NOT NULL,
            local_commit_sha TEXT NOT NULL, remote_commit_sha TEXT, branch_name TEXT NOT NULL,
            status TEXT NOT NULL, pr_number INTEGER, pr_url TEXT, title TEXT, summary TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            UNIQUE (tenant_id, id)
        )""")
        adapter.execute("""CREATE TABLE IF NOT EXISTS engineering_change_files (
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, change_set_id TEXT NOT NULL,
            path TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
            UNIQUE (tenant_id, change_set_id, path)
        )""")
        adapter.execute("CREATE INDEX IF NOT EXISTS idx_change_sets_tenant_created ON engineering_change_sets(tenant_id, created_at DESC)")
        adapter.execute("CREATE INDEX IF NOT EXISTS idx_change_files_set ON engineering_change_files(tenant_id, change_set_id)")
        adapter.execute("""CREATE TABLE IF NOT EXISTS engineering_agent_runs (
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, workspace_id TEXT NOT NULL,
            plan JSONB NOT NULL, status TEXT NOT NULL,
            completed_steps JSONB NOT NULL DEFAULT '[]'::jsonb, failed_step TEXT,
            repair_count INTEGER NOT NULL DEFAULT 0,
            evidence JSONB NOT NULL DEFAULT '[]'::jsonb, idempotency_key TEXT,
            correlation_id TEXT, authorization_id TEXT, active_step_id TEXT,
            active_token TEXT, lease_until TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE (tenant_id, idempotency_key)
        )""")
        adapter.execute("CREATE INDEX IF NOT EXISTS idx_agent_runs_tenant_created ON engineering_agent_runs(tenant_id, created_at DESC)")
        adapter.execute("""CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, title TEXT NOT NULL,
            repository_id TEXT, workspace_id TEXT, mode TEXT NOT NULL CHECK (mode IN ('ask','plan','execute')),
            created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
            UNIQUE (tenant_id, id)
        )""")
        adapter.execute("""CREATE TABLE IF NOT EXISTS conversation_messages (
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, conversation_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('user','assistant')), content TEXT NOT NULL,
            message_type TEXT NOT NULL DEFAULT 'text', metadata JSONB, created_at TIMESTAMPTZ NOT NULL,
            UNIQUE (tenant_id, id),
            FOREIGN KEY (tenant_id, conversation_id) REFERENCES conversations (tenant_id, id) ON DELETE CASCADE
        )""")
        adapter.execute("CREATE INDEX IF NOT EXISTS idx_conversations_tenant_updated ON conversations (tenant_id, updated_at DESC)")
        adapter.execute("CREATE INDEX IF NOT EXISTS idx_conversation_messages_tenant_conversation ON conversation_messages (tenant_id, conversation_id, created_at)")
        adapter.execute("ALTER TABLE conversations ENABLE ROW LEVEL SECURITY")
        adapter.execute("ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY")
        adapter.execute("ALTER TABLE conversations FORCE ROW LEVEL SECURITY")
        adapter.execute("ALTER TABLE conversation_messages FORCE ROW LEVEL SECURITY")
        adapter.execute("DROP POLICY IF EXISTS conversations_tenant_isolation ON conversations")
        adapter.execute("""CREATE POLICY conversations_tenant_isolation ON conversations
            USING (tenant_id = current_setting('oae.tenant_id', true))
            WITH CHECK (tenant_id = current_setting('oae.tenant_id', true))""")
        adapter.execute("DROP POLICY IF EXISTS conversation_messages_tenant_isolation ON conversation_messages")
        adapter.execute("""CREATE POLICY conversation_messages_tenant_isolation ON conversation_messages
            USING (tenant_id = current_setting('oae.tenant_id', true))
            WITH CHECK (tenant_id = current_setting('oae.tenant_id', true))""")
        adapter.execute("CREATE INDEX IF NOT EXISTS idx_agent_runs_workspace ON engineering_agent_runs(tenant_id, workspace_id, created_at DESC)")
        adapter.commit()
        _POSTGRES_BOOTSTRAPPED_URLS.add(database_url)


@contextmanager
def db(tenant_id: str | None = None):
    conn = _connect(tenant_id)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
