CREATE TABLE IF NOT EXISTS engineering_change_sets (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    source_revision_id TEXT NOT NULL,
    local_commit_sha TEXT NOT NULL,
    remote_commit_sha TEXT,
    branch_name TEXT NOT NULL,
    status TEXT NOT NULL,
    pr_number INTEGER,
    pr_url TEXT,
    title TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS engineering_change_files (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    change_set_id TEXT NOT NULL,
    path TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, change_set_id, path)
);

CREATE INDEX IF NOT EXISTS idx_change_sets_tenant_created
    ON engineering_change_sets (tenant_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_change_files_set
    ON engineering_change_files (tenant_id, change_set_id);
