"""PostgreSQL-backed job queue operations with lease-token fencing and transactional events."""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from oae.api.config import settings
from oae.api.db import db
from oae.api.domain_events import DomainEventWriter


class DurableJobsError(RuntimeError):
    """Base error for durable queue coordination failures."""


class LeaseLost(DurableJobsError):
    """Raised when a worker tries to mutate a job without holding its active lease."""


@dataclass(frozen=True)
class EnqueuedJob:
    id: str
    tenant_id: str
    status: str
    operation: str
    payload: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created: bool


@dataclass(frozen=True)
class JobLease:
    job_id: str
    tenant_id: str
    operation: str
    payload: dict[str, Any]
    worker_id: str
    lease_token: str
    attempt_number: int
    max_attempts: int
    lease_expires_at: datetime


class DurableJobRepository:
    """Coordinates durable jobs while keeping state mutation and outbox writing atomic."""

    def __init__(self, event_writer: DomainEventWriter | None = None):
        self.event_writer = event_writer or DomainEventWriter()

    def enqueue(
        self,
        *,
        tenant_id: str,
        operation: str,
        payload: dict[str, Any],
        idempotency_key: str | None = None,
        workspace_id: str | None = None,
        priority: int = 100,
        correlation_id: str | None = None,
    ) -> EnqueuedJob:
        self._require_postgres()
        if not 0 <= priority <= 1000:
            raise DurableJobsError("Job priority must be between 0 and 1000.")
        job_id = str(uuid4())
        now = datetime.now(timezone.utc)
        with db() as conn:
            row = conn.execute(
                """
                INSERT INTO jobs(
                    id,tenant_id,status,operation,payload,created_at,updated_at,workspace_id,
                    idempotency_key,priority,attempt_count,max_attempts,scheduled_at,correlation_id
                ) VALUES(?,?, 'queued', ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                ON CONFLICT(tenant_id,idempotency_key) WHERE idempotency_key IS NOT NULL DO NOTHING
                RETURNING id,tenant_id,status,operation,payload,created_at,updated_at
                """,
                (
                    job_id,
                    tenant_id,
                    operation,
                    json.dumps(payload, separators=(",", ":"), sort_keys=True),
                    now,
                    now,
                    workspace_id,
                    idempotency_key,
                    priority,
                    settings.durable_job_max_attempts,
                    now,
                    correlation_id,
                ),
            ).fetchone()
            if row:
                self.event_writer.append(
                    conn,
                    tenant_id=tenant_id,
                    aggregate_type="job",
                    aggregate_id=job_id,
                    event_type="job.queued",
                    payload={
                        "operation": operation,
                        "priority": priority,
                        "workspace_id": workspace_id,
                    },
                    correlation_id=correlation_id,
                    occurred_at=now,
                )
                return self._enqueued(row, created=True)
            existing = conn.execute(
                """
                SELECT id,tenant_id,status,operation,payload,created_at,updated_at
                FROM jobs WHERE tenant_id=? AND idempotency_key=?
                """,
                (tenant_id, idempotency_key),
            ).fetchone()
            if not existing:
                raise DurableJobsError("Job enqueue did not return an idempotency outcome.")
            return self._enqueued(existing, created=False)

    def register_worker(
        self,
        *,
        worker_name: str,
        pool: str = "engineering",
        version: str = "0.6.0",
        capabilities: dict[str, Any] | None = None,
    ) -> str:
        self._require_postgres()
        with db() as conn:
            row = conn.execute(
                """
                INSERT INTO workers(id,worker_name,pool,version,capabilities,state,last_heartbeat_at,started_at)
                VALUES(?,?,?,?,?::jsonb,'ready',now(),now())
                ON CONFLICT(worker_name)
                DO UPDATE SET pool=EXCLUDED.pool,version=EXCLUDED.version,
                    capabilities=EXCLUDED.capabilities,state='ready',last_heartbeat_at=now(),stopped_at=NULL
                RETURNING id
                """,
                (
                    str(uuid4()),
                    worker_name,
                    pool,
                    version,
                    json.dumps(capabilities or {}, separators=(",", ":"), sort_keys=True),
                ),
            ).fetchone()
        return str(row[0])

    def claim_next(self, worker_id: str) -> JobLease | None:
        self._require_postgres()
        token = str(uuid4())
        with db() as conn:
            row = conn.execute(
                """
                WITH candidate AS (
                    SELECT id FROM jobs
                    WHERE status IN ('queued','retry_scheduled') AND scheduled_at <= now()
                    ORDER BY priority ASC,scheduled_at ASC,created_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE jobs AS job
                SET status='running',worker_id=?,lease_token=?,
                    lease_expires_at=now() + (? * interval '1 second'),
                    attempt_count=job.attempt_count+1,updated_at=now()
                FROM candidate
                WHERE job.id=candidate.id
                RETURNING job.id,job.tenant_id,job.operation,job.payload,job.attempt_count,
                    job.max_attempts,job.lease_expires_at
                """,
                (worker_id, token, settings.durable_job_lease_seconds),
            ).fetchone()
            if not row:
                return None
            lease = JobLease(
                job_id=str(row[0]),
                tenant_id=str(row[1]),
                operation=str(row[2]),
                payload=json.loads(row[3]),
                worker_id=worker_id,
                lease_token=token,
                attempt_number=int(row[4]),
                max_attempts=int(row[5]),
                lease_expires_at=self._as_datetime(row[6]),
            )
            conn.execute(
                """
                INSERT INTO job_attempts(id,tenant_id,job_id,attempt_number,worker_id,lease_token,status,started_at)
                VALUES(?,?,?,?,?,?, 'running', now())
                """,
                (
                    str(uuid4()),
                    lease.tenant_id,
                    lease.job_id,
                    lease.attempt_number,
                    worker_id,
                    token,
                ),
            )
            self.event_writer.append(
                conn,
                tenant_id=lease.tenant_id,
                aggregate_type="job",
                aggregate_id=lease.job_id,
                event_type="job.claimed",
                payload={"attempt_number": lease.attempt_number, "worker_id": worker_id},
            )
            self.event_writer.append(
                conn,
                tenant_id=lease.tenant_id,
                aggregate_type="job",
                aggregate_id=lease.job_id,
                event_type="job.running",
                payload={"attempt_number": lease.attempt_number},
            )
        return lease

    def renew_lease(self, lease: JobLease) -> datetime:
        self._require_postgres()
        with db() as conn:
            row = conn.execute(
                """
                UPDATE jobs SET lease_expires_at=now() + (? * interval '1 second'),updated_at=now()
                WHERE id=? AND tenant_id=? AND worker_id=? AND lease_token=?
                    AND status='running' AND lease_expires_at > now()
                RETURNING lease_expires_at
                """,
                (
                    settings.durable_job_lease_seconds,
                    lease.job_id,
                    lease.tenant_id,
                    lease.worker_id,
                    lease.lease_token,
                ),
            ).fetchone()
        if not row:
            raise LeaseLost("The worker no longer owns this job lease.")
        return self._as_datetime(row[0])

    def complete(self, lease: JobLease, result: dict[str, Any]) -> None:
        self._finish(lease, status="completed", result=result, failure_code=None)

    def fail(self, lease: JobLease, failure_code: str) -> None:
        self._finish(lease, status="failed", result=None, failure_code=failure_code)

    def retry(self, lease: JobLease, failure_code: str) -> datetime:
        self._require_postgres()
        if lease.attempt_number >= lease.max_attempts:
            raise DurableJobsError("A retry cannot be scheduled after the final allowed attempt.")
        retry_at = datetime.now(timezone.utc) + timedelta(
            seconds=min(settings.durable_job_retry_max_seconds, 2 ** lease.attempt_number)
        )
        with db() as conn:
            changed = conn.execute(
                """
                UPDATE jobs
                SET status='retry_scheduled',scheduled_at=?,worker_id=NULL,lease_token=NULL,
                    lease_expires_at=NULL,failure_code=?,updated_at=?
                WHERE id=? AND tenant_id=? AND worker_id=? AND lease_token=?
                    AND status='running' AND lease_expires_at > now()
                """,
                (
                    retry_at,
                    failure_code,
                    datetime.now(timezone.utc),
                    lease.job_id,
                    lease.tenant_id,
                    lease.worker_id,
                    lease.lease_token,
                ),
            ).rowcount
            if changed != 1:
                raise LeaseLost("The worker no longer owns this job lease.")
            conn.execute(
                """
                UPDATE job_attempts SET status='failed',ended_at=now(),retry_at=?,error_class=?
                WHERE tenant_id=? AND job_id=? AND worker_id=? AND lease_token=? AND status='running'
                """,
                (retry_at, failure_code, lease.tenant_id, lease.job_id, lease.worker_id, lease.lease_token),
            )
            self.event_writer.append(
                conn,
                tenant_id=lease.tenant_id,
                aggregate_type="job",
                aggregate_id=lease.job_id,
                event_type="job.retry_scheduled",
                payload={"attempt_number": lease.attempt_number, "retry_at": retry_at.isoformat()},
                correlation_id=None,
            )
        return retry_at

    def recover_expired_leases(self, limit: int = 100) -> int:
        self._require_postgres()
        if limit < 1 or limit > 1000:
            raise DurableJobsError("Recovery limit must be between 1 and 1000.")
        recovered = 0
        with db() as conn:
            rows = conn.execute(
                """
                SELECT id,tenant_id,attempt_count,max_attempts FROM jobs
                WHERE status='running' AND lease_expires_at < now()
                ORDER BY lease_expires_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            for row in rows:
                job_id, tenant_id, attempt_count, max_attempts = (
                    str(row[0]),
                    str(row[1]),
                    int(row[2]),
                    int(row[3]),
                )
                terminal = attempt_count >= max_attempts
                next_status = "failed" if terminal else "retry_scheduled"
                retry_at = None if terminal else datetime.now(timezone.utc) + timedelta(
                    seconds=min(settings.durable_job_retry_max_seconds, 2 ** attempt_count)
                )
                changed = conn.execute(
                    """
                    UPDATE jobs SET status=?,scheduled_at=COALESCE(?,scheduled_at),worker_id=NULL,
                        lease_token=NULL,lease_expires_at=NULL,failure_code='lease_expired',
                        completed_at=CASE WHEN ? THEN now() ELSE completed_at END,updated_at=now()
                    WHERE id=? AND tenant_id=? AND status='running' AND lease_expires_at < now()
                    """,
                    (next_status, retry_at, terminal, job_id, tenant_id),
                ).rowcount
                if changed != 1:
                    continue
                conn.execute(
                    """
                    UPDATE job_attempts SET status='abandoned',ended_at=now(),error_class='lease_expired'
                    WHERE tenant_id=? AND job_id=? AND status='running'
                    """,
                    (tenant_id, job_id),
                )
                self.event_writer.append(
                    conn,
                    tenant_id=tenant_id,
                    aggregate_type="job",
                    aggregate_id=job_id,
                    event_type="job.failed" if terminal else "job.retry_scheduled",
                    payload={"failure_code": "lease_expired", "attempt_number": attempt_count},
                )
                recovered += 1
        return recovered

    def _finish(
        self,
        lease: JobLease,
        *,
        status: str,
        result: dict[str, Any] | None,
        failure_code: str | None,
    ) -> None:
        self._require_postgres()
        with db() as conn:
            changed = conn.execute(
                """
                UPDATE jobs SET status=?,result=?,failure_code=?,completed_at=now(),worker_id=NULL,
                    lease_token=NULL,lease_expires_at=NULL,updated_at=now()
                WHERE id=? AND tenant_id=? AND worker_id=? AND lease_token=?
                    AND status='running' AND lease_expires_at > now()
                """,
                (
                    status,
                    json.dumps(result, separators=(",", ":"), sort_keys=True) if result else None,
                    failure_code,
                    lease.job_id,
                    lease.tenant_id,
                    lease.worker_id,
                    lease.lease_token,
                ),
            ).rowcount
            if changed != 1:
                raise LeaseLost("The worker no longer owns this job lease.")
            conn.execute(
                """
                UPDATE job_attempts SET status=?,ended_at=now(),error_class=?
                WHERE tenant_id=? AND job_id=? AND worker_id=? AND lease_token=? AND status='running'
                """,
                (
                    "succeeded" if status == "completed" else "failed",
                    failure_code,
                    lease.tenant_id,
                    lease.job_id,
                    lease.worker_id,
                    lease.lease_token,
                ),
            )
            self.event_writer.append(
                conn,
                tenant_id=lease.tenant_id,
                aggregate_type="job",
                aggregate_id=lease.job_id,
                event_type="job.completed" if status == "completed" else "job.failed",
                payload={"attempt_number": lease.attempt_number, "failure_code": failure_code},
            )

    @staticmethod
    def _enqueued(row, *, created: bool) -> EnqueuedJob:
        return EnqueuedJob(
            id=str(row[0]),
            tenant_id=str(row[1]),
            status=str(row[2]),
            operation=str(row[3]),
            payload=json.loads(row[4]),
            created_at=DurableJobRepository._as_datetime(row[5]),
            updated_at=DurableJobRepository._as_datetime(row[6]),
            created=created,
        )

    @staticmethod
    def _as_datetime(value: datetime | str) -> datetime:
        return value if isinstance(value, datetime) else datetime.fromisoformat(value)

    @staticmethod
    def _require_postgres() -> None:
        if settings.database_backend != "postgres":
            raise DurableJobsError("Durable job leasing requires PostgreSQL and applied OAE migrations.")
