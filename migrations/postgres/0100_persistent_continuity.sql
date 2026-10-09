-- Durable project context, user-controlled memory, tasks, runs and checkpoints.
-- Additive only: existing conversations and engineering runs are preserved.
CREATE TABLE IF NOT EXISTS oae_projects (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'planning' CHECK (status IN ('planning','active','paused','blocked','completed','archived')),
    repository_ref TEXT,
    summary TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    UNIQUE (tenant_id, id)
);
CREATE TABLE IF NOT EXISTS oae_memory_records (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    project_id TEXT,
    category TEXT NOT NULL CHECK (category IN ('preference','project','working','reference')),
    content TEXT NOT NULL,
    source_conversation_id TEXT,
    source_message_id TEXT,
    confidence TEXT NOT NULL DEFAULT 'unverified' CHECK (confidence IN ('confirmed','user_approved','unverified')),
    sensitivity TEXT NOT NULL DEFAULT 'normal' CHECK (sensitivity IN ('normal','private','sensitive')),
    state TEXT NOT NULL DEFAULT 'active' CHECK (state IN ('active','superseded','deleted')),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, project_id) REFERENCES oae_projects(tenant_id, id)
);
CREATE TABLE IF NOT EXISTS oae_tasks (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','in_progress','blocked','completed','cancelled')),
    dependencies JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, project_id) REFERENCES oae_projects(tenant_id, id)
);
CREATE TABLE IF NOT EXISTS oae_execution_runs (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    project_id TEXT NOT NULL,
    task_id TEXT,
    conversation_id TEXT,
    objective TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('initialized','running','paused','blocked','failed','interrupted','completed','cancelled')),
    plan JSONB NOT NULL DEFAULT '[]'::jsonb,
    completed_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    pending_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    current_step TEXT,
    blockers JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    errors JSONB NOT NULL DEFAULT '[]'::jsonb,
    retry_count INTEGER NOT NULL DEFAULT 0,
    lease_owner TEXT,
    lease_until TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, idempotency_key),
    FOREIGN KEY (tenant_id, project_id) REFERENCES oae_projects(tenant_id, id),
    FOREIGN KEY (tenant_id, task_id) REFERENCES oae_tasks(tenant_id, id)
);
CREATE TABLE IF NOT EXISTS oae_checkpoints (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    project_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('running','completed','failed','blocked','interrupted','paused')),
    label TEXT NOT NULL,
    state_snapshot JSONB NOT NULL,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, run_id, sequence),
    FOREIGN KEY (tenant_id, project_id) REFERENCES oae_projects(tenant_id, id),
    FOREIGN KEY (tenant_id, run_id) REFERENCES oae_execution_runs(tenant_id, id)
);
CREATE TABLE IF NOT EXISTS oae_decisions (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    project_id TEXT NOT NULL,
    conversation_id TEXT,
    title TEXT NOT NULL,
    decision JSONB NOT NULL,
    rationale TEXT NOT NULL DEFAULT '',
    source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    state TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id, project_id) REFERENCES oae_projects(tenant_id, id)
);
CREATE INDEX IF NOT EXISTS idx_oae_projects_tenant_activity ON oae_projects(tenant_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_oae_memory_lookup ON oae_memory_records(tenant_id, category, state, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_oae_tasks_project ON oae_tasks(tenant_id, project_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_oae_runs_project ON oae_execution_runs(tenant_id, project_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_oae_checkpoints_run ON oae_checkpoints(tenant_id, run_id, sequence DESC);
CREATE INDEX IF NOT EXISTS idx_oae_decisions_project ON oae_decisions(tenant_id, project_id, created_at DESC);
DO $$
DECLARE table_name text;
BEGIN
    FOREACH table_name IN ARRAY ARRAY['oae_projects','oae_memory_records','oae_tasks','oae_execution_runs','oae_checkpoints','oae_decisions'] LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);
        EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', table_name);
        EXECUTE format('DROP POLICY IF EXISTS oae_tenant_isolation ON %I', table_name);
        EXECUTE format(
            'CREATE POLICY oae_tenant_isolation ON %I USING (tenant_id = current_setting(''oae.tenant_id'', true)) WITH CHECK (tenant_id = current_setting(''oae.tenant_id'', true))',
            table_name
        );
    END LOOP;
END $$;
