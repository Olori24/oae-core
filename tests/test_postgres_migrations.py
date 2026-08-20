from oae.api.migrations import migration_files


def test_postgres_migration_files_are_ordered_and_present():
    names = [path.name for path in migration_files()]

    assert names == [
        "0001_workspace_foundation.sql",
        "0002_durable_job_worker_foundation.sql",
        "0003_transactional_outbox_sse.sql",
    ]


def test_workspace_migration_declares_tenant_scoped_persistence():
    migration = migration_files()[0].read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS workspaces" in migration
    assert "CREATE TABLE IF NOT EXISTS workspace_manifest_entries" in migration
    assert "tenant_id TEXT NOT NULL" in migration
    assert "retention_expires_at TIMESTAMPTZ NOT NULL" in migration


def test_worker_migration_declares_leases_attempts_and_outbox():
    migration = migration_files()[1].read_text(encoding="utf-8")

    assert "lease_token TEXT" in migration
    assert "CREATE TABLE IF NOT EXISTS job_attempts" in migration
    assert "CREATE TABLE IF NOT EXISTS outbox_events" in migration


def test_outbox_sse_migration_declares_durable_replay_and_relay_leases():
    migration = migration_files()[2].read_text(encoding="utf-8")

    assert "ADD COLUMN IF NOT EXISTS tenant_sequence BIGINT" in migration
    assert "ADD COLUMN IF NOT EXISTS aggregate_sequence BIGINT" in migration
    assert "relay_lease_token TEXT" in migration
    assert "ck_outbox_event_sequences_paired" in migration
    assert "CREATE TABLE IF NOT EXISTS tenant_event_cursors" in migration
    assert "CREATE TABLE IF NOT EXISTS aggregate_event_cursors" in migration
    assert "CREATE TABLE IF NOT EXISTS tenant_event_publication_cursors" in migration
    assert "CREATE TABLE IF NOT EXISTS realtime_events" in migration
    assert "UNIQUE (tenant_id, tenant_sequence)" in migration
    assert "UNIQUE (tenant_id, aggregate_type, aggregate_id, aggregate_sequence)" in migration
    assert "CREATE UNIQUE INDEX IF NOT EXISTS uq_outbox_events_tenant_sequence" in migration
    assert "CREATE UNIQUE INDEX IF NOT EXISTS uq_outbox_events_aggregate_sequence" in migration
    assert "CREATE OR REPLACE FUNCTION oae_notify_realtime_event()" in migration
    assert "PERFORM pg_notify('oae_realtime_event', NEW.id)" in migration
