from contextlib import contextmanager

import pytest

from oae.api.worker_authorizations import WorkerAuthorizationError, WorkerAuthorizationRepository


class _Result:
    def __init__(self, row=None, rowcount=1):
        self._row = row
        self.rowcount = rowcount

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self):
        self.calls = []
        self.decision_row = ("build",)

    def execute(self, query, params=()):
        self.calls.append((query, params))
        if "UPDATE worker_authorizations" in query:
            return _Result(self.decision_row)
        return _Result()


class _EventWriter:
    def __init__(self):
        self.events = []

    def append(self, _conn, **kwargs):
        self.events.append(kwargs)


@contextmanager
def _fake_db(connection):
    yield connection


@pytest.fixture
def postgres_settings(monkeypatch):
    import oae.api.worker_authorizations as module

    monkeypatch.setattr(module.settings, "database_url", "postgresql://example/oae")


def test_request_persists_pending_tenant_scoped_authorization_and_outbox_event(monkeypatch, postgres_settings):
    import oae.api.worker_authorizations as module

    connection = _Connection()
    writer = _EventWriter()
    monkeypatch.setattr(module, "db", lambda: _fake_db(connection))

    record = WorkerAuthorizationRepository(writer).request(
        tenant_id="tenant-1",
        operation="build",
        scope={"repository_id": "repo-1"},
        requester="operator-1",
        expires_in_seconds=3600,
    )

    assert record.tenant_id == "tenant-1"
    assert record.operation == "build"
    assert record.status == "pending"
    assert writer.events[0]["event_type"] == "authorization.requested"
    assert any("INSERT INTO worker_authorizations" in query for query, _ in connection.calls)


def test_approval_records_actor_and_emits_durable_event(monkeypatch, postgres_settings):
    import oae.api.worker_authorizations as module

    connection = _Connection()
    writer = _EventWriter()
    monkeypatch.setattr(module, "db", lambda: _fake_db(connection))

    WorkerAuthorizationRepository(writer).approve(
        tenant_id="tenant-1",
        authorization_id="authorization-1",
        approver="approver-1",
        approver_role="approver",
        decision_reason_redacted="scope reviewed",
    )

    assert writer.events[0]["event_type"] == "authorization.approved"
    assert writer.events[0]["payload"] == {
        "operation": "build",
        "approver": "approver-1",
        "approver_role": "approver",
    }
    assert any("status='pending'" in query for query, _ in connection.calls)


def test_approval_rejects_missing_expired_or_already_decided_record(monkeypatch, postgres_settings):
    import oae.api.worker_authorizations as module

    connection = _Connection()
    connection.decision_row = None
    monkeypatch.setattr(module, "db", lambda: _fake_db(connection))

    with pytest.raises(WorkerAuthorizationError, match="missing, expired, already decided, or cannot be self-approved"):
        WorkerAuthorizationRepository(_EventWriter()).approve(
            tenant_id="tenant-1",
            authorization_id="authorization-1",
            approver="approver-1",
            approver_role="approver",
        )


def test_postgres_requirement_rejects_sqlite_without_storing_authorization(monkeypatch):
    import oae.api.worker_authorizations as module

    monkeypatch.setattr(module.settings, "database_url", "sqlite:///./oae.db")
    with pytest.raises(WorkerAuthorizationError, match="requires PostgreSQL"):
        WorkerAuthorizationRepository(_EventWriter()).request(
            tenant_id="tenant-1",
            operation="build",
            scope={},
            requester="operator-1",
            expires_in_seconds=3600,
        )
