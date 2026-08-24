"""Durable, tenant-scoped authorization records for governed worker execution."""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from oae.api.config import settings
from oae.api.db import db
from oae.api.domain_events import DomainEventWriter


class WorkerAuthorizationError(RuntimeError):
    """Raised when an authorization record cannot satisfy a governed action."""


@dataclass(frozen=True)
class WorkerAuthorization:
    id: str
    tenant_id: str
    operation: str
    scope: dict[str, str]
    requester: str
    status: str
    requested_at: datetime
    expires_at: datetime
    decided_at: datetime | None
    decided_by: str | None
    decided_role: str | None
    decision_reason_redacted: str | None
    revoked_at: datetime | None
    revoked_by: str | None
    revoked_role: str | None


class WorkerAuthorizationRepository:
    """Persists authorization lifecycle records and emits a durable audit event per transition."""

    def __init__(self, event_writer: DomainEventWriter | None = None):
        self.event_writer = event_writer or DomainEventWriter()

    def request(
        self,
        *,
        tenant_id: str,
        operation: str,
        scope: dict[str, str],
        requester: str,
        expires_in_seconds: int,
    ) -> WorkerAuthorization:
        self._require_postgres()
        if not 60 <= expires_in_seconds <= 7 * 24 * 60 * 60:
            raise WorkerAuthorizationError("Authorization expiry must be between 60 seconds and 7 days.")
        authorization_id = str(uuid4())
        requested_at = datetime.now(timezone.utc)
        expires_at = requested_at + timedelta(seconds=expires_in_seconds)
        with db() as conn:
            conn.execute(
                """
                INSERT INTO worker_authorizations(
                    id,tenant_id,operation,scope,requester,status,requested_at,expires_at
                ) VALUES(?,?,?,?,?,'pending',?,?)
                """,
                (
                    authorization_id,
                    tenant_id,
                    operation,
                    json.dumps(scope, separators=(",", ":"), sort_keys=True),
                    requester,
                    requested_at,
                    expires_at,
                ),
            )
            self.event_writer.append(
                conn,
                tenant_id=tenant_id,
                aggregate_type="authorization",
                aggregate_id=authorization_id,
                event_type="authorization.requested",
                payload={"operation": operation, "requester": requester, "scope_keys": sorted(scope)},
                occurred_at=requested_at,
            )
        return WorkerAuthorization(
            id=authorization_id,
            tenant_id=tenant_id,
            operation=operation,
            scope=scope,
            requester=requester,
            status="pending",
            requested_at=requested_at,
            expires_at=expires_at,
            decided_at=None,
            decided_by=None,
            decided_role=None,
            decision_reason_redacted=None,
            revoked_at=None,
            revoked_by=None,
            revoked_role=None,
        )

    def get(self, *, tenant_id: str, authorization_id: str) -> WorkerAuthorization | None:
        self._require_postgres()
        with db() as conn:
            row = conn.execute(
                """
                SELECT id,tenant_id,operation,scope,requester,status,requested_at,expires_at,
                       decided_at,decided_by,decided_role,decision_reason_redacted,
                       revoked_at,revoked_by,revoked_role
                FROM worker_authorizations WHERE tenant_id=? AND id=?
                """,
                (tenant_id, authorization_id),
            ).fetchone()
        return self._record(row) if row else None

    def approve(
        self,
        *,
        tenant_id: str,
        authorization_id: str,
        approver: str,
        approver_role: str = "approver",
        decision_reason_redacted: str | None = None,
    ) -> None:
        self._decide(
            tenant_id=tenant_id,
            authorization_id=authorization_id,
            approver=approver,
            approver_role=approver_role,
            next_status="approved",
            decision_reason_redacted=decision_reason_redacted,
        )

    def reject(
        self,
        *,
        tenant_id: str,
        authorization_id: str,
        approver: str,
        approver_role: str = "approver",
        decision_reason_redacted: str | None = None,
    ) -> None:
        self._decide(
            tenant_id=tenant_id,
            authorization_id=authorization_id,
            approver=approver,
            approver_role=approver_role,
            next_status="rejected",
            decision_reason_redacted=decision_reason_redacted,
        )

    def revoke(
        self,
        *,
        tenant_id: str,
        authorization_id: str,
        approver: str,
        approver_role: str = "approver",
    ) -> None:
        self._require_postgres()
        now = datetime.now(timezone.utc)
        with db() as conn:
            row = conn.execute(
                """
                UPDATE worker_authorizations
                SET status='revoked',revoked_at=?,revoked_by=?,revoked_role=?
                WHERE id=? AND tenant_id=? AND status='approved' AND expires_at > now()
                RETURNING operation
                """,
                (now, approver, approver_role, authorization_id, tenant_id),
            ).fetchone()
            if not row:
                raise WorkerAuthorizationError("Authorization is missing, expired, or not revocable.")
            self.event_writer.append(
                conn,
                tenant_id=tenant_id,
                aggregate_type="authorization",
                aggregate_id=authorization_id,
                event_type="authorization.revoked",
                payload={"operation": str(row[0]), "approver": approver, "approver_role": approver_role},
                occurred_at=now,
            )

    def is_approved_for_execution(
        self, *, tenant_id: str, authorization_id: str | None, operation: str
    ) -> bool:
        self._require_postgres()
        if not authorization_id:
            return False
        with db() as conn:
            row = conn.execute(
                """
                SELECT 1 FROM worker_authorizations
                WHERE id=? AND tenant_id=? AND operation=? AND status='approved' AND expires_at > now()
                """,
                (authorization_id, tenant_id, operation),
            ).fetchone()
        return bool(row)

    def _decide(
        self,
        *,
        tenant_id: str,
        authorization_id: str,
        approver: str,
        approver_role: str,
        next_status: str,
        decision_reason_redacted: str | None,
    ) -> None:
        self._require_postgres()
        now = datetime.now(timezone.utc)
        with db() as conn:
            row = conn.execute(
                """
                UPDATE worker_authorizations
                SET status=?,decided_at=?,decided_by=?,decided_role=?,decision_reason_redacted=?
                WHERE id=? AND tenant_id=? AND status='pending' AND expires_at > now() AND requester<>?
                RETURNING operation
                """,
                (
                    next_status,
                    now,
                    approver,
                    approver_role,
                    decision_reason_redacted,
                    authorization_id,
                    tenant_id,
                    approver,
                ),
            ).fetchone()
            if not row:
                raise WorkerAuthorizationError(
                    "Authorization is missing, expired, already decided, or cannot be self-approved."
                )
            self.event_writer.append(
                conn,
                tenant_id=tenant_id,
                aggregate_type="authorization",
                aggregate_id=authorization_id,
                event_type=f"authorization.{next_status}",
                payload={"operation": str(row[0]), "approver": approver, "approver_role": approver_role},
                occurred_at=now,
            )

    @staticmethod
    def _record(row: Any) -> WorkerAuthorization:
        scope = row[3]
        if isinstance(scope, str):
            scope = json.loads(scope)
        return WorkerAuthorization(
            id=str(row[0]),
            tenant_id=str(row[1]),
            operation=str(row[2]),
            scope={str(key): str(value) for key, value in dict(scope).items()},
            requester=str(row[4]),
            status=str(row[5]),
            requested_at=WorkerAuthorizationRepository._as_datetime(row[6]),
            expires_at=WorkerAuthorizationRepository._as_datetime(row[7]),
            decided_at=WorkerAuthorizationRepository._as_datetime(row[8]) if row[8] else None,
            decided_by=str(row[9]) if row[9] else None,
            decided_role=str(row[10]) if row[10] else None,
            decision_reason_redacted=str(row[11]) if row[11] else None,
            revoked_at=WorkerAuthorizationRepository._as_datetime(row[12]) if row[12] else None,
            revoked_by=str(row[13]) if row[13] else None,
            revoked_role=str(row[14]) if row[14] else None,
        )

    @staticmethod
    def _as_datetime(value: datetime | str) -> datetime:
        return value if isinstance(value, datetime) else datetime.fromisoformat(value)

    @staticmethod
    def _require_postgres() -> None:
        if settings.database_backend != "postgres":
            raise WorkerAuthorizationError("Worker authorization requires PostgreSQL and applied OAE migrations.")
