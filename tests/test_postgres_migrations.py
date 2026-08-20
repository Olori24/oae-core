from oae.api.migrations import migration_files


def test_postgres_migration_files_are_ordered_and_present():
    names = [path.name for path in migration_files()]

    assert names == [
        "0001_workspace_foundation.sql",
        "0002_durable_job_worker_foundation.sql",
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
