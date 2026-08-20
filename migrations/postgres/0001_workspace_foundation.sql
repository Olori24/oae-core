-- OAE persistent repository workspace foundation.
-- This migration is PostgreSQL-only and is recorded by oae.api.migrations.

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
);

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
    size_bytes BIGINT NOT NULL DEFAULT 0 CHECK (size_bytes >= 0),
    file_count INTEGER NOT NULL DEFAULT 0 CHECK (file_count >= 0),
    retention_expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ready_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    failure_code TEXT,
    failure_detail_redacted TEXT,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, repository_id)
        REFERENCES repositories (tenant_id, id),
    FOREIGN KEY (tenant_id, source_revision_id)
        REFERENCES repository_revisions (tenant_id, id),
    FOREIGN KEY (tenant_id, parent_workspace_id)
        REFERENCES workspaces (tenant_id, id)
);

CREATE INDEX IF NOT EXISTS idx_repositories_tenant_active
    ON repositories (tenant_id, status, created_at DESC)
    WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_workspace_expiry
    ON workspaces (tenant_id, retention_expires_at)
    WHERE state IN ('ready', 'failed');
CREATE INDEX IF NOT EXISTS idx_workspace_repository_state
    ON workspaces (tenant_id, repository_id, state, created_at DESC);

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
    FOREIGN KEY (tenant_id, workspace_id)
        REFERENCES workspaces (tenant_id, id)
);

CREATE INDEX IF NOT EXISTS idx_workspace_manifest_listing
    ON workspace_manifest_entries (tenant_id, workspace_id, relative_path);
