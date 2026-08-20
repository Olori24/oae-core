-- OAE durable job leasing, retry history, and transactional event foundation.

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS workspace_id TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS idempotency_key TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS priority SMALLINT NOT NULL DEFAULT 100;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS max_attempts INTEGER NOT NULL DEFAULT 3;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS worker_id TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS lease_token TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS lease_expires_at TIMESTAMPTZ;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS cancel_requested_at TIMESTAMPTZ;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS failure_code TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS correlation_id TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_jobs_tenant_id'
    ) THEN
        ALTER TABLE jobs ADD CONSTRAINT uq_jobs_tenant_id UNIQUE (tenant_id, id);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_jobs_workspace'
    ) THEN
        ALTER TABLE jobs
            ADD CONSTRAINT fk_jobs_workspace
            FOREIGN KEY (tenant_id, workspace_id)
            REFERENCES workspaces (tenant_id, id);
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_jobs_tenant_idempotency
    ON jobs (tenant_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jobs_claimable
    ON jobs (status, scheduled_at, priority, created_at)
    WHERE status IN ('queued', 'retry_scheduled');
CREATE INDEX IF NOT EXISTS idx_jobs_lease_expiry
    ON jobs (lease_expires_at)
    WHERE status = 'running';

CREATE TABLE IF NOT EXISTS workers (
    id TEXT PRIMARY KEY,
    worker_name TEXT NOT NULL UNIQUE,
    pool TEXT NOT NULL,
    version TEXT NOT NULL,
    capabilities JSONB NOT NULL DEFAULT '{}'::jsonb,
    state TEXT NOT NULL CHECK (state IN ('starting', 'ready', 'draining', 'offline')),
    last_heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    stopped_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS job_attempts (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    job_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL CHECK (attempt_number > 0),
    worker_id TEXT REFERENCES workers(id),
    lease_token TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('claimed', 'running', 'succeeded', 'failed', 'abandoned', 'cancelled')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    retry_at TIMESTAMPTZ,
    exit_code INTEGER,
    error_class TEXT,
    error_detail_redacted TEXT,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (tenant_id, job_id, attempt_number),
    FOREIGN KEY (tenant_id, job_id) REFERENCES jobs (tenant_id, id)
);

CREATE INDEX IF NOT EXISTS idx_job_attempts_job
    ON job_attempts (tenant_id, job_id, attempt_number DESC);

CREATE TABLE IF NOT EXISTS outbox_events (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ,
    publish_attempts INTEGER NOT NULL DEFAULT 0,
    next_publish_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_outbox_publishable
    ON outbox_events (next_publish_at, occurred_at)
    WHERE published_at IS NULL;

CREATE TABLE IF NOT EXISTS job_events (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    job_id TEXT NOT NULL,
    sequence BIGINT NOT NULL CHECK (sequence > 0),
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, job_id, sequence),
    FOREIGN KEY (tenant_id, job_id) REFERENCES jobs (tenant_id, id)
);
