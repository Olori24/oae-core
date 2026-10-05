ALTER TABLE engineering_agent_runs
    ADD COLUMN IF NOT EXISTS authorization_id TEXT,
    ADD COLUMN IF NOT EXISTS active_step_id TEXT,
    ADD COLUMN IF NOT EXISTS active_token TEXT,
    ADD COLUMN IF NOT EXISTS lease_until TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_agent_runs_active_lease
    ON engineering_agent_runs (tenant_id, status, lease_until);
