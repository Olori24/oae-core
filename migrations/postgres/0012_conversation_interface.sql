CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, title TEXT NOT NULL,
    repository_id TEXT, workspace_id TEXT, mode TEXT NOT NULL CHECK (mode IN ('ask','plan','execute')),
    created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (tenant_id, id)
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user','assistant')), content TEXT NOT NULL,
    message_type TEXT NOT NULL DEFAULT 'text', metadata JSONB, created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, conversation_id) REFERENCES conversations (tenant_id, id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conversations_tenant_updated ON conversations (tenant_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_tenant_conversation ON conversation_messages (tenant_id, conversation_id, created_at);

ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations FORCE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS conversations_tenant_isolation ON conversations;
CREATE POLICY conversations_tenant_isolation ON conversations
    USING (tenant_id = current_setting('oae.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('oae.tenant_id', true));

DROP POLICY IF EXISTS conversation_messages_tenant_isolation ON conversation_messages;
CREATE POLICY conversation_messages_tenant_isolation ON conversation_messages
    USING (tenant_id = current_setting('oae.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('oae.tenant_id', true));
