"""PostgreSQL end-to-end concurrency coverage for transactional outbox projection and SSE replay."""

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from oae.api.app import app
from oae.api.db import db
from oae.api.domain_events import DomainEventWriter
from oae.api.outbox_relay import OutboxRelay
from oae.api.realtime_events import RealtimeEventStore
from tests.postgres_integration import postgres_connection

pytestmark = pytest.mark.postgres_integration


def _create_tenant(client: TestClient, name: str) -> tuple[str, str]:
    response = client.post("/v1/tenants", json={"name": name})
    assert response.status_code == 201
    body = response.json()
    return body["tenant_id"], body["api_key"]


def _insert_job(tenant_id: str, job_id: str) -> None:
    now = datetime.now(timezone.utc)
    with db() as conn:
        conn.execute(
            """
            INSERT INTO jobs(id,tenant_id,status,operation,payload,created_at,updated_at)
            VALUES(?,?, 'completed', 'build', '{}', ?, ?)
            """,
            (job_id, tenant_id, now, now),
        )


def _append_events(tenant_id: str, count: int) -> None:
    writer = DomainEventWriter()
    _insert_job(tenant_id, f"job-{tenant_id}")
    for position in range(1, count + 1):
        with db() as conn:
            writer.append(
                conn,
                tenant_id=tenant_id,
                aggregate_type="job",
                aggregate_id=f"job-{tenant_id}",
                event_type="job.progress",
                payload={"tenant_marker": tenant_id, "position": position},
                correlation_id=f"load-{tenant_id}",
            )


def _drain_relay(expected: int) -> None:
    deadline = time.monotonic() + 10
    projected = 0
    while time.monotonic() < deadline:
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda index: OutboxRelay(f"relay-{index}").run_once(4), range(4)))
        projected += sum(result.projected for result in results)
        if projected >= expected:
            return
        time.sleep(1.05)
    raise AssertionError("Concurrent relay workers did not project the expected event batch.")


def _rows(url: str, query: str, params=()):
    with postgres_connection(url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def test_concurrent_tenants_preserve_sequences_and_atomic_outbox_projection(postgres_schema):
    with TestClient(app) as client:
        tenants = [_create_tenant(client, f"Tenant {index}") for index in range(3)]
    tenant_ids = [tenant_id for tenant_id, _ in tenants]
    events_per_tenant = 6
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda tenant_id: _append_events(tenant_id, events_per_tenant), tenant_ids))

    _drain_relay(expected=len(tenant_ids) * events_per_tenant)

    outbox = _rows(
        postgres_schema,
        """
        SELECT tenant_id,tenant_sequence,published_at IS NOT NULL
        FROM outbox_events ORDER BY tenant_id,tenant_sequence
        """,
    )
    replay = _rows(
        postgres_schema,
        "SELECT tenant_id,tenant_sequence FROM realtime_events ORDER BY tenant_id,tenant_sequence",
    )
    assert len(outbox) == len(tenant_ids) * events_per_tenant
    assert len(replay) == len(outbox)
    for tenant_id in tenant_ids:
        sequences = [row[1] for row in outbox if row[0] == tenant_id]
        assert sequences == list(range(1, events_per_tenant + 1))
        assert all(row[2] for row in outbox if row[0] == tenant_id)

    store = RealtimeEventStore()
    for tenant_id in tenant_ids:
        events = store.list_tenant_events(tenant_id, after=0)
        assert [event.tenant_sequence for event in events] == list(range(1, events_per_tenant + 1))
        assert {event.payload["tenant_marker"] for event in events} == {tenant_id}


def test_transaction_rollback_leaves_no_orphan_outbox_event(postgres_schema):
    with TestClient(app) as client:
        tenant_id, _ = _create_tenant(client, "Rollback Tenant")
    writer = DomainEventWriter()
    with pytest.raises(RuntimeError):
        with db() as conn:
            writer.append(
                conn,
                tenant_id=tenant_id,
                aggregate_type="job",
                aggregate_id="job-rollback",
                event_type="job.queued",
                payload={"tenant_marker": tenant_id},
            )
            raise RuntimeError("force rollback")

    rows = _rows(postgres_schema, "SELECT id FROM outbox_events WHERE tenant_id=?", (tenant_id,))
    assert rows == []


def test_authenticated_sse_streams_are_tenant_isolated_under_concurrent_load(postgres_schema):
    with TestClient(app) as client:
        tenants = [_create_tenant(client, f"Stream Tenant {index}") for index in range(3)]
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda tenant: _append_events(tenant[0], 3), tenants))
    _drain_relay(expected=9)

    def consume(tenant):
        tenant_id, api_key = tenant
        with TestClient(app) as client:
            response = client.get("/v1/events", headers={"Authorization": f"Bearer {api_key}"})
        return tenant_id, response

    with ThreadPoolExecutor(max_workers=3) as pool:
        streams = list(pool.map(consume, tenants))
    for tenant_id, response in streams:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert "tenant_id" not in response.text
        assert f'"tenant_marker":"{tenant_id}"' in response.text
        for foreign_tenant, _ in tenants:
            if foreign_tenant != tenant_id:
                assert foreign_tenant not in response.text


def test_job_sse_replay_rejects_foreign_tenant_resource(postgres_schema):
    with TestClient(app) as client:
        owner_id, _ = _create_tenant(client, "Owner")
        _, foreign_key = _create_tenant(client, "Foreign")
    job_id = str(uuid4())
    _insert_job(owner_id, job_id)
    _append_events(owner_id, 1)
    _drain_relay(expected=1)

    with TestClient(app) as client:
        response = client.get(
            f"/v1/jobs/{job_id}/events",
            headers={"Authorization": f"Bearer {foreign_key}"},
        )
    assert response.status_code == 404
