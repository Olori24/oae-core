CREATE TABLE IF NOT EXISTS engineering_agent_runs (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    plan JSONB NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('running', 'complete', 'failed', 'blocked')),
    completed_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    failed_step TEXT,
    repair_count INTEGER NOT NULL DEFAULT 0 CHECK (repair_count >= 0 AND repair_count <= 3),
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    idempotency_key TEXT,
    correlation_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_tenant_created
    ON engineering_agent_runs (tenant_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_runs_workspace
    ON engineering_agent_runs (tenant_id, workspace_id, created_at DESC);
