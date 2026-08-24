-- OAE principal roles and separation-of-duties metadata for worker authorization decisions.

ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS principal_id TEXT;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS principal_role TEXT;

ALTER TABLE worker_authorizations ADD COLUMN IF NOT EXISTS decided_role TEXT;
ALTER TABLE worker_authorizations ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ;
ALTER TABLE worker_authorizations ADD COLUMN IF NOT EXISTS revoked_by TEXT;
ALTER TABLE worker_authorizations ADD COLUMN IF NOT EXISTS revoked_role TEXT;

CREATE INDEX IF NOT EXISTS idx_api_keys_tenant_principal
    ON api_keys (tenant_id, principal_id)
    WHERE revoked_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_worker_authorizations_revocable
    ON worker_authorizations (tenant_id, status, expires_at)
    WHERE status = 'approved';
