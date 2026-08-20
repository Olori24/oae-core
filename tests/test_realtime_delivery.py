import json
from contextlib import contextmanager
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from oae.api.app import app
from oae.api.outbox_relay import OutboxEvent, OutboxRelay
from oae.api.realtime_events import EventCursorExpired, RealtimeEvent, RealtimeEventStore


class _Result:
    def __init__(self, row=None, rows=None, rowcount=1):
        self._row = row
        self._rows = rows or []
        self.rowcount = rowcount

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class RelayConnection:
    def __init__(self, publication_cursor=0):
        self.publication_cursor = publication_cursor
        self.calls = []

    def execute(self, query, params=()):
        self.calls.append((query, params))
        if "SELECT id,tenant_sequence FROM outbox_events" in query:
            return _Result(("event-1", 1))
        if "INSERT INTO tenant_event_publication_cursors" in query:
            return _Result((self.publication_cursor,))
        if "UPDATE outbox_events\n                SET published_at" in query:
            return _Result(rowcount=1)
        if "SELECT publish_attempts FROM outbox_events" in query:
            return _Result((2,))
        return _Result()


@contextmanager
def _fake_db(connection):
    yield connection


@pytest.fixture
def postgres_relay(monkeypatch):
    import oae.api.outbox_relay as module

    monkeypatch.setattr(module.settings, "database_url", "postgresql://example/oae")


def _event(sequence=1):
    return OutboxEvent(
        id="event-1",
        tenant_id="tenant-1",
        aggregate_type="job",
        aggregate_id="job-1",
        event_type="job.completed",
        payload={"attempt_number": 1},
        occurred_at=datetime.now(timezone.utc),
        tenant_sequence=sequence,
        aggregate_sequence=1,
        correlation_id="correlation-1",
        causation_id=None,
        lease_token="lease-1",
    )


def test_relay_projects_one_ordered_event_and_job_projection(monkeypatch, postgres_relay):
    import oae.api.outbox_relay as module

    connection = RelayConnection(publication_cursor=0)
    monkeypatch.setattr(module, "db", lambda: _fake_db(connection))

    assert OutboxRelay("relay-1").project(_event()) is True
    queries = [query for query, _ in connection.calls]
    assert any("INSERT INTO realtime_events" in query for query in queries)
    assert any("INSERT INTO job_events" in query for query in queries)
    assert any("last_published_sequence=?" in query for query in queries)
    assert any("SET published_at=now()" in query for query in queries)


def test_relay_releases_a_later_event_until_its_tenant_predecessor_is_published(
    monkeypatch, postgres_relay
):
    import oae.api.outbox_relay as module

    connection = RelayConnection(publication_cursor=0)
    monkeypatch.setattr(module, "db", lambda: _fake_db(connection))

    assert OutboxRelay("relay-1").project(_event(sequence=2)) is False
    assert not any("INSERT INTO realtime_events" in query for query, _ in connection.calls)
    assert any("next_publish_at=now() + interval '1 second'" in query for query, _ in connection.calls)


def test_relay_failure_record_is_redacted_and_releases_its_lease(monkeypatch, postgres_relay):
    import oae.api.outbox_relay as module

    connection = RelayConnection()
    monkeypatch.setattr(module, "db", lambda: _fake_db(connection))
    OutboxRelay("relay-1").record_failure(_event(), RuntimeError("secret://must-not-persist"))

    failure_update = next(
        params for query, params in connection.calls if "last_error_redacted" in query
    )
    assert failure_update[0] == "RuntimeError: projection_failed"
    assert "secret" not in failure_update[0]


class ReplayConnection:
    def __init__(self, oldest=1, rows=None, owned=True):
        self.oldest = oldest
        self.rows = rows or []
        self.owned = owned

    def execute(self, query, _params=()):
        if "MIN(tenant_sequence)" in query or "MIN(aggregate_sequence)" in query:
            return _Result((self.oldest,))
        if "SELECT 1 FROM" in query:
            return _Result((1,) if self.owned else None)
        if "FROM realtime_events" in query:
            return _Result(rows=self.rows)
        if "COALESCE(MAX(tenant_sequence),0)" in query:
            return _Result((3,))
        if "FROM jobs" in query or "FROM workspaces" in query:
            return _Result(rows=[])
        return _Result()


@pytest.fixture
def realtime_enabled(monkeypatch):
    import oae.api.realtime_events as module

    monkeypatch.setattr(module.settings, "database_url", "postgresql://example/oae")
    monkeypatch.setattr(module.settings, "realtime_events_enabled", True)


def test_replay_envelope_hides_tenant_identifier_and_expired_cursor_is_rejected(
    monkeypatch, realtime_enabled
):
    import oae.api.realtime_events as module

    row = (
        "event-1", 2, "workspace", "workspace-1", 1, "workspace.ready", json.dumps({"file_count": 2}),
        datetime.now(timezone.utc), "correlation-1", None,
    )
    connection = ReplayConnection(oldest=2, rows=[row])
    monkeypatch.setattr(module, "db", lambda: _fake_db(connection))
    store = RealtimeEventStore()

    event = store.list_tenant_events("tenant-1", after=1)[0]
    envelope = event.envelope()
    assert envelope["tenant_sequence"] == 2
    assert "tenant_id" not in envelope
    with pytest.raises(EventCursorExpired) as exc_info:
        store.list_tenant_events("tenant-1", after=0)
    assert exc_info.value.oldest_sequence == 2


def test_realtime_store_checks_aggregate_ownership(monkeypatch, realtime_enabled):
    import oae.api.realtime_events as module

    monkeypatch.setattr(module, "db", lambda: _fake_db(ReplayConnection(owned=False)))
    assert RealtimeEventStore().assert_aggregate_owned("tenant-1", "job", "job-1") is False


def test_authenticated_sse_route_emits_durable_event_and_hides_foreign_aggregate(monkeypatch, tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database
    import oae.api.routes as routes

    db_path = tmp_path / "sse-routes.db"
    monkeypatch.setattr(database.settings, "database_url", f"sqlite:///{db_path}")
    monkeypatch.setattr(auth.settings, "database_url", f"sqlite:///{db_path}")
    monkeypatch.setattr(routes.settings, "sse_max_connection_seconds", 0.02)
    monkeypatch.setattr(routes.settings, "sse_poll_seconds", 0.01)

    class Store:
        def list_tenant_events(self, _tenant_id, _after):
            return [
                RealtimeEvent(
                    id="event-1",
                    tenant_sequence=1,
                    aggregate_type="workspace",
                    aggregate_id="workspace-1",
                    aggregate_sequence=1,
                    event_type="workspace.ready",
                    payload={"file_count": 2},
                    occurred_at=datetime.now(timezone.utc),
                    correlation_id=None,
                    causation_id=None,
                )
            ]

        def assert_aggregate_owned(self, *_args):
            return False

        def list_aggregate_events(self, *_args):
            return []

        def snapshot(self, _tenant_id):
            return {"cursor": 1, "jobs": [], "workspaces": []}

    monkeypatch.setattr(routes, "RealtimeEventStore", Store)
    client = TestClient(app)
    tenant = client.post("/v1/tenants", json={"name": "SSE Tenant"})
    headers = {"Authorization": f"Bearer {tenant.json()['api_key']}"}

    response = client.get("/v1/events", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: workspace.ready" in response.text
    assert "tenant_id" not in response.text
    assert client.get("/v1/workspaces/foreign/events", headers=headers).status_code == 404
