-- OAE governed execution: tenant-scoped authorization requests for worker-executed jobs.

CREATE TABLE IF NOT EXISTS worker_authorizations (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    operation TEXT NOT NULL,
    scope JSONB NOT NULL DEFAULT '{}'::jsonb,
    requester TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected', 'revoked', 'expired')),
    requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    decided_at TIMESTAMPTZ,
    decided_by TEXT,
    decision_reason_redacted TEXT,
    UNIQUE (tenant_id, id)
);

CREATE INDEX IF NOT EXISTS idx_worker_authorizations_active
    ON worker_authorizations (tenant_id, operation, expires_at)
    WHERE status = 'approved';

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS authorization_id TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_jobs_worker_authorization'
    ) THEN
        ALTER TABLE jobs
        ADD CONSTRAINT fk_jobs_worker_authorization
        FOREIGN KEY (tenant_id, authorization_id)
        REFERENCES worker_authorizations (tenant_id, id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_jobs_authorization_id
    ON jobs (tenant_id, authorization_id)
    WHERE authorization_id IS NOT NULL;
