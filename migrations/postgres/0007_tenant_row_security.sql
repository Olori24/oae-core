-- Tenant isolation for the PostgreSQL API role.
-- The API role must not have BYPASSRLS. The worker role uses a separate connection
-- and is intentionally privileged for cross-tenant queue coordination.
--
-- PostgreSQL applies RLS policies only when RLS is enabled; FORCE RLS also applies
-- policies to the table owner. See PostgreSQL CREATE POLICY / ALTER TABLE docs.

DO $$
DECLARE
    table_name text;
    tenant_tables text[] := ARRAY[
        'jobs',
        'repositories',
        'repository_revisions',
        'workspaces',
        'workspace_manifest_entries',
        'job_attempts',
        'outbox_events',
        'job_events',
        'worker_authorizations',
        'tenant_event_cursors',
        'aggregate_event_cursors',
        'tenant_event_publication_cursors',
        'realtime_events'
    ];
BEGIN
    FOREACH table_name IN ARRAY tenant_tables LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);
        EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', table_name);
        EXECUTE format(
            'DROP POLICY IF EXISTS oae_tenant_isolation ON %I',
            table_name
        );
        EXECUTE format(
            'CREATE POLICY oae_tenant_isolation ON %I
             USING (tenant_id = current_setting(''oae.tenant_id'', true))
             WITH CHECK (tenant_id = current_setting(''oae.tenant_id'', true))',
            table_name
        );
    END LOOP;
END $$;

CREATE INDEX IF NOT EXISTS idx_rate_limit_buckets_expiry
    ON rate_limit_buckets(window_start);
