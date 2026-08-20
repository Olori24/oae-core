import json
from contextlib import contextmanager
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from oae.api.app import app
from oae.api.domain_events import DomainEventError, DomainEventWriter
from oae.api.durable_jobs import DurableJobRepository, JobLease, LeaseLost
from oae.api.durable_worker import DurableWorker


class _Result:
    def __init__(self, row=None, rows=None, rowcount=1):
        self._row = row
        self._rows = rows or []
        self.rowcount = rowcount

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class _Connection:
    def __init__(self):
        self.calls = []
        self.job_insert_row = None
        self.existing_job_row = None
        self.claim_row = None
        self.renew_row = None
        self.finish_rowcount = 1
        self.recovery_rows = []
        self.tenant_sequence = 0
        self.aggregate_sequence = 0
        self.outbox_event_types = []

    def execute(self, query, params=()):
        self.calls.append((query, params))
        if "INSERT INTO tenant_event_cursors" in query:
            self.tenant_sequence += 1
            return _Result((self.tenant_sequence,))
        if "INSERT INTO aggregate_event_cursors" in query:
            self.aggregate_sequence += 1
            return _Result((self.aggregate_sequence,))
        if "INSERT INTO outbox_events" in query:
            self.outbox_event_types.append(params[4])
            return _Result()
        if "INSERT INTO jobs(" in query:
            return _Result(self.job_insert_row)
        if "FROM jobs WHERE tenant_id=? AND idempotency_key=?" in query:
            return _Result(self.existing_job_row)
        if "WITH candidate AS" in query:
            return _Result(self.claim_row)
        if "UPDATE jobs SET lease_expires_at" in query:
            return _Result(self.renew_row)
        if "UPDATE jobs SET status=?" in query:
            return _Result(rowcount=self.finish_rowcount)
        if "SELECT id,tenant_id,attempt_count,max_attempts FROM jobs" in query:
            return _Result(rows=self.recovery_rows)
        return _Result()


@contextmanager
def _fake_db(connection):
    yield connection


@pytest.fixture
def postgres_settings(monkeypatch):
    import oae.api.durable_jobs as durable_jobs

    monkeypatch.setattr(durable_jobs.settings, "database_url", "postgresql://example/oae")


def test_domain_event_writer_allocates_sequences_and_uses_given_transaction():
    connection = _Connection()
    event = DomainEventWriter().append(
        connection,
        tenant_id="tenant-1",
        aggregate_type="job",
        aggregate_id="job-1",
        event_type="job.queued",
        payload={"operation": "build"},
        correlation_id="correlation-1",
    )

    assert event.tenant_sequence == 1
    assert event.aggregate_sequence == 1
    assert connection.outbox_event_types == ["job.queued"]
    assert sum("tenant_event_cursors" in query for query, _ in connection.calls) == 1
    assert sum("aggregate_event_cursors" in query for query, _ in connection.calls) == 1
    assert sum("outbox_events" in query for query, _ in connection.calls) == 1


def test_domain_event_writer_rejects_unserializable_or_oversized_payloads():
    writer = DomainEventWriter()

    with pytest.raises(DomainEventError):
        writer.append(
            _Connection(),
            tenant_id="tenant-1",
            aggregate_type="job",
            aggregate_id="job-1",
            event_type="job.queued",
            payload={"unserializable": object()},
        )
    with pytest.raises(DomainEventError):
        writer.append(
            _Connection(),
            tenant_id="tenant-1",
            aggregate_type="job",
            aggregate_id="job-1",
            event_type="job.queued",
            payload={"large": "x" * (32 * 1024)},
        )


def test_durable_enqueue_writes_job_and_event_in_one_connection(monkeypatch, postgres_settings):
    import oae.api.durable_jobs as module

    now = datetime.now(timezone.utc)
    connection = _Connection()
    connection.job_insert_row = ("job-1", "tenant-1", "queued", "build", "{}", now, now)
    monkeypatch.setattr(module, "db", lambda: _fake_db(connection))

    job = DurableJobRepository().enqueue(
        tenant_id="tenant-1",
        operation="build",
        payload={},
        idempotency_key="request-1",
        correlation_id="correlation-1",
    )

    assert job.created is True
    assert job.id == "job-1"
    assert connection.outbox_event_types == ["job.queued"]
    assert any("INSERT INTO jobs(" in query for query, _ in connection.calls)


def test_durable_enqueue_returns_existing_idempotency_outcome_without_second_event(
    monkeypatch, postgres_settings
):
    import oae.api.durable_jobs as module

    now = datetime.now(timezone.utc)
    connection = _Connection()
    connection.existing_job_row = ("job-1", "tenant-1", "queued", "build", "{}", now, now)
    monkeypatch.setattr(module, "db", lambda: _fake_db(connection))

    job = DurableJobRepository().enqueue(
        tenant_id="tenant-1",
        operation="build",
        payload={},
        idempotency_key="request-1",
    )

    assert job.created is False
    assert connection.outbox_event_types == []


def test_claim_records_attempt_emits_events_and_lease_fences_completion(monkeypatch, postgres_settings):
    import oae.api.durable_jobs as module

    now = datetime.now(timezone.utc)
    connection = _Connection()
    connection.claim_row = ("job-1", "tenant-1", "build", json.dumps({}), 1, 3, now)
    monkeypatch.setattr(module, "db", lambda: _fake_db(connection))
    repository = DurableJobRepository()

    lease = repository.claim_next("worker-1")

    assert lease is not None
    assert lease.job_id == "job-1"
    assert lease.max_attempts == 3
    assert connection.outbox_event_types == ["job.claimed", "job.running"]
    assert any("INSERT INTO job_attempts" in query for query, _ in connection.calls)

    connection.finish_rowcount = 0
    with pytest.raises(LeaseLost):
        repository.complete(lease, {"status": "ok"})
    assert connection.outbox_event_types == ["job.claimed", "job.running"]


def test_lease_renewal_rejects_a_lost_or_expired_lease(monkeypatch, postgres_settings):
    import oae.api.durable_jobs as module

    connection = _Connection()
    monkeypatch.setattr(module, "db", lambda: _fake_db(connection))
    lease = JobLease(
        job_id="job-1",
        tenant_id="tenant-1",
        operation="build",
        payload={},
        worker_id="worker-1",
        lease_token="token-1",
        attempt_number=1,
        max_attempts=3,
        lease_expires_at=datetime.now(timezone.utc),
    )

    with pytest.raises(LeaseLost):
        DurableJobRepository().renew_lease(lease)


def test_expired_lease_recovery_schedules_retry_and_emits_event(monkeypatch, postgres_settings):
    import oae.api.durable_jobs as module

    connection = _Connection()
    connection.recovery_rows = [("job-1", "tenant-1", 1, 3)]
    monkeypatch.setattr(module, "db", lambda: _fake_db(connection))

    assert DurableJobRepository().recover_expired_leases() == 1
    assert connection.outbox_event_types == ["job.retry_scheduled"]
    assert any("UPDATE job_attempts SET status='abandoned'" in query for query, _ in connection.calls)


def test_durable_worker_respects_max_attempts_without_hard_coded_limit():
    lease = JobLease(
        job_id="job-1",
        tenant_id="tenant-1",
        operation="build",
        payload={},
        worker_id="worker-1",
        lease_token="token-1",
        attempt_number=4,
        max_attempts=4,
        lease_expires_at=datetime.now(timezone.utc),
    )

    class Repository:
        def __init__(self):
            self.failed = []

        def claim_next(self, _worker_id):
            return lease

        def fail(self, current_lease, failure_code):
            self.failed.append((current_lease, failure_code))

        def retry(self, *_args):
            raise AssertionError("Final attempt must not be retried")

        def renew_lease(self, _lease):
            return datetime.now(timezone.utc)

    repository = Repository()
    worker = DurableWorker(repository, "worker-1")
    worker.runner._dispatch = lambda *_args: (_ for _ in ()).throw(RuntimeError("boom"))

    assert worker.run_once() is True
    assert repository.failed == [(lease, "worker_execution_failed")]


def test_enabled_durable_dispatch_rejects_sqlite_instead_of_falling_back(monkeypatch, tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database
    import oae.api.routes as routes

    db_path = tmp_path / "durable-feature.db"
    monkeypatch.setattr(database.settings, "database_url", f"sqlite:///{db_path}")
    monkeypatch.setattr(auth.settings, "database_url", f"sqlite:///{db_path}")
    monkeypatch.setattr(routes.settings, "durable_jobs_enabled", True)
    client = TestClient(app)
    tenant = client.post("/v1/tenants", json={"name": "Durable Tenant"})

    response = client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {tenant.json()['api_key']}"},
        json={"operation": "build", "payload": {"name": "Demo", "description": "Demo job"}},
    )

    assert response.status_code == 503
