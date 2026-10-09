-- User-controlled history metadata; message and conversation rows remain intact unless explicitly deleted.
CREATE TABLE IF NOT EXISTS oae_conversation_state (
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    conversation_id TEXT NOT NULL,
    archived_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, conversation_id),
    FOREIGN KEY (tenant_id, conversation_id) REFERENCES conversations(tenant_id, id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_oae_conversation_state_archive ON oae_conversation_state(tenant_id, archived_at, updated_at DESC);
ALTER TABLE oae_conversation_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE oae_conversation_state FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS oae_tenant_isolation ON oae_conversation_state;
CREATE POLICY oae_tenant_isolation ON oae_conversation_state
USING (tenant_id = current_setting('oae.tenant_id', true))
WITH CHECK (tenant_id = current_setting('oae.tenant_id', true));
