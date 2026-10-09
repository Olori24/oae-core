import os
from contextlib import contextmanager
from uuid import uuid4

import pytest

from oae.api.migrations import (
    CREATE_MIGRATION_TABLE_SQL,
    INSERT_MIGRATION_SQL,
    SELECT_APPLIED_MIGRATIONS_SQL,
    apply_postgres_migrations,
    migration_files,
)
from oae.api.db import _ConnectionAdapter, _bootstrap_postgres


class _MigrationCursor:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=()):
        self.calls.append((query, params))

    def fetchall(self):
        return []


class _MigrationConnection:
    def __init__(self):
        self.cursor_instance = _MigrationCursor()
        self.committed = False

    @contextmanager
    def cursor(self):
        yield self.cursor_instance

    def commit(self):
        self.committed = True


def test_postgres_migration_files_are_ordered_and_present():
    names = [path.name for path in migration_files()]

    assert names == [
        "0001_workspace_foundation.sql",
        "0002_durable_job_worker_foundation.sql",
        "0003_transactional_outbox_sse.sql",
        "0004_realtime_event_metadata.sql",
        "0005_worker_authorization_foundation.sql",
        "0006_principal_and_authorization_decision_metadata.sql",
        "0007_tenant_row_security.sql",
        "0008_job_result_payload.sql",
        "0009_engineering_change_sets.sql",
        "0010_engineering_agent_runs.sql",
        "0011_agent_run_execution_leases.sql",
        "0012_conversation_interface.sql",
        "0013_greenfield_workspaces.sql",
        "0100_persistent_continuity.sql",
        "0101_conversation_history_controls.sql",
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


def test_realtime_event_metadata_migration_preserves_correlation_fields():
    migration = migration_files()[3].read_text(encoding="utf-8")

    assert "ALTER TABLE realtime_events ADD COLUMN IF NOT EXISTS correlation_id TEXT" in migration
    assert "ALTER TABLE realtime_events ADD COLUMN IF NOT EXISTS causation_id TEXT" in migration


def test_worker_authorization_migration_binds_approvals_to_tenant_scoped_jobs():
    migration = migration_files()[4].read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS worker_authorizations" in migration
    assert "tenant_id TEXT NOT NULL REFERENCES tenants(id)" in migration
    assert "status IN ('pending', 'approved', 'rejected', 'revoked', 'expired')" in migration
    assert "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS authorization_id TEXT" in migration
    assert "FOREIGN KEY (tenant_id, authorization_id)" in migration


def test_principal_role_migration_tracks_decision_and_revocation_metadata():
    migration = migration_files()[5].read_text(encoding="utf-8")

    assert "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS principal_id TEXT" in migration
    assert "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS principal_role TEXT" in migration
    assert "ALTER TABLE worker_authorizations ADD COLUMN IF NOT EXISTS decided_role TEXT" in migration
    assert "ALTER TABLE worker_authorizations ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ" in migration


def test_migration_ledger_uses_fixed_queries_for_its_fixed_table_name():
    connection = _MigrationConnection()

    assert apply_postgres_migrations(connection, migrations=[]) == []
    queries = [query for query, _ in connection.cursor_instance.calls]

    assert queries == [CREATE_MIGRATION_TABLE_SQL, SELECT_APPLIED_MIGRATIONS_SQL]
    assert "{" not in CREATE_MIGRATION_TABLE_SQL
    assert "{" not in SELECT_APPLIED_MIGRATIONS_SQL
    assert "%s" in INSERT_MIGRATION_SQL
    assert connection.committed is True


@pytest.mark.postgres_integration
@pytest.mark.skipif(not os.environ.get("OAE_POSTGRES_TEST_URL"), reason="isolated PostgreSQL test URL not configured")
def test_all_postgres_migrations_apply_in_an_isolated_schema():
    import psycopg

    schema = f"oae_migration_test_{uuid4().hex}"
    with psycopg.connect(os.environ["OAE_POSTGRES_TEST_URL"]) as connection:
        connection.execute(f'CREATE SCHEMA "{schema}"')
        try:
            connection.execute(f'SET search_path TO "{schema}"')
            # Reuse the same base-schema bootstrap used by the API and migration CLI.
            _bootstrap_postgres(
                _ConnectionAdapter(connection, "postgres"),
                os.environ["OAE_POSTGRES_TEST_URL"] + "#schema=" + schema,
            )
            applied = apply_postgres_migrations(connection)
            expected = [path.name for path in migration_files()]
            assert applied == expected

            rows = connection.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
                (schema,),
            ).fetchall()
            tables = {row[0] for row in rows}
            assert {
                "oae_projects",
                "oae_memory_records",
                "oae_tasks",
                "oae_execution_runs",
                "oae_checkpoints",
                "oae_decisions",
                "oae_conversation_state",
            } <= tables
            ledger = connection.execute(
                "SELECT name FROM oae_schema_migrations ORDER BY name"
            ).fetchall()
            assert {row[0] for row in ledger} == set(expected)
        finally:
            connection.execute("SET search_path TO public")
            connection.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
