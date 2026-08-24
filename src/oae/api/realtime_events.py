"""Tenant-authorized replay reads for durable outbox projections and SSE streams."""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from oae.api.config import settings
from oae.api.db import db


class RealtimeEventsError(RuntimeError):
    """Base error for realtime replay availability and validation failures."""


class EventCursorExpired(RealtimeEventsError):
    """Raised when a reconnect cursor predates retained durable replay events."""

    def __init__(self, oldest_sequence: int):
        self.oldest_sequence = oldest_sequence
        super().__init__("The requested event cursor has expired.")


AGGREGATE_OWNERSHIP_QUERIES = {
    "job": "SELECT 1 FROM jobs WHERE id=? AND tenant_id=?",
    "workspace": "SELECT 1 FROM workspaces WHERE id=? AND tenant_id=?",
}


@dataclass(frozen=True)
class RealtimeEvent:
    id: str
    tenant_sequence: int
    aggregate_type: str
    aggregate_id: str
    aggregate_sequence: int
    event_type: str
    payload: dict[str, Any]
    occurred_at: datetime | str
    correlation_id: str | None
    causation_id: str | None

    def envelope(self) -> dict[str, Any]:
        occurred_at = self.occurred_at.isoformat() if isinstance(self.occurred_at, datetime) else self.occurred_at
        return {
            "schema_version": "1.0",
            "event_id": self.id,
            "tenant_sequence": self.tenant_sequence,
            "aggregate": {
                "type": self.aggregate_type,
                "id": self.aggregate_id,
                "sequence": self.aggregate_sequence,
            },
            "event_type": self.event_type,
            "occurred_at": occurred_at,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "data": self.payload,
        }


class RealtimeEventStore:
    """Reads immutable, tenant-owned events; all state-changing delivery remains in the relay."""

    def list_tenant_events(self, tenant_id: str, after: int, limit: int | None = None) -> list[RealtimeEvent]:
        self._require_available()
        self._validate_cursor(after)
        resolved_limit = self._limit(limit)
        with db() as conn:
            oldest = conn.execute(
                "SELECT MIN(tenant_sequence) FROM realtime_events WHERE tenant_id=?", (tenant_id,)
            ).fetchone()[0]
            if oldest is not None and after < int(oldest) - 1:
                raise EventCursorExpired(int(oldest))
            rows = conn.execute(
                """
                SELECT id,tenant_sequence,aggregate_type,aggregate_id,aggregate_sequence,event_type,
                    payload,occurred_at,correlation_id,causation_id
                FROM realtime_events
                WHERE tenant_id=? AND tenant_sequence > ?
                ORDER BY tenant_sequence ASC
                LIMIT ?
                """,
                (tenant_id, after, resolved_limit),
            ).fetchall()
        return [self._event(row) for row in rows]

    def list_aggregate_events(
        self,
        tenant_id: str,
        aggregate_type: str,
        aggregate_id: str,
        after: int,
        limit: int | None = None,
    ) -> list[RealtimeEvent]:
        self._require_available()
        self._validate_cursor(after)
        resolved_limit = self._limit(limit)
        with db() as conn:
            oldest = conn.execute(
                """
                SELECT MIN(aggregate_sequence) FROM realtime_events
                WHERE tenant_id=? AND aggregate_type=? AND aggregate_id=?
                """,
                (tenant_id, aggregate_type, aggregate_id),
            ).fetchone()[0]
            if oldest is not None and after < int(oldest) - 1:
                raise EventCursorExpired(int(oldest))
            rows = conn.execute(
                """
                SELECT id,tenant_sequence,aggregate_type,aggregate_id,aggregate_sequence,event_type,
                    payload,occurred_at,correlation_id,causation_id
                FROM realtime_events
                WHERE tenant_id=? AND aggregate_type=? AND aggregate_id=? AND aggregate_sequence > ?
                ORDER BY aggregate_sequence ASC
                LIMIT ?
                """,
                (tenant_id, aggregate_type, aggregate_id, after, resolved_limit),
            ).fetchall()
        return [self._event(row) for row in rows]

    def snapshot(self, tenant_id: str) -> dict[str, Any]:
        self._require_available()
        with db() as conn:
            cursor = conn.execute(
                "SELECT COALESCE(MAX(tenant_sequence),0) FROM realtime_events WHERE tenant_id=?",
                (tenant_id,),
            ).fetchone()[0]
            jobs = conn.execute(
                """
                SELECT id,status,operation,updated_at FROM jobs
                WHERE tenant_id=? ORDER BY updated_at DESC LIMIT 100
                """,
                (tenant_id,),
            ).fetchall()
            workspaces = conn.execute(
                """
                SELECT id,state,purpose,COALESCE(ready_at,deleted_at,created_at) FROM workspaces
                WHERE tenant_id=? ORDER BY COALESCE(ready_at,deleted_at,created_at) DESC LIMIT 100
                """,
                (tenant_id,),
            ).fetchall()
        return {
            "cursor": int(cursor),
            "jobs": [
                {"id": str(row[0]), "status": str(row[1]), "operation": str(row[2]), "updated_at": row[3]}
                for row in jobs
            ],
            "workspaces": [
                {"id": str(row[0]), "state": str(row[1]), "purpose": str(row[2]), "updated_at": row[3]}
                for row in workspaces
            ],
        }

    def assert_aggregate_owned(self, tenant_id: str, aggregate_type: str, aggregate_id: str) -> bool:
        self._require_available()
        query = AGGREGATE_OWNERSHIP_QUERIES.get(aggregate_type)
        if query is None:
            return False
        with db() as conn:
            row = conn.execute(
                query,
                (aggregate_id, tenant_id),
            ).fetchone()
        return row is not None

    @staticmethod
    def _event(row) -> RealtimeEvent:
        payload = row[6]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return RealtimeEvent(
            id=str(row[0]),
            tenant_sequence=int(row[1]),
            aggregate_type=str(row[2]),
            aggregate_id=str(row[3]),
            aggregate_sequence=int(row[4]),
            event_type=str(row[5]),
            payload=payload,
            occurred_at=row[7],
            correlation_id=row[8],
            causation_id=row[9],
        )

    @staticmethod
    def _validate_cursor(after: int) -> None:
        if after < 0:
            raise RealtimeEventsError("Event cursor must not be negative.")

    @staticmethod
    def _limit(limit: int | None) -> int:
        value = settings.sse_replay_limit if limit is None else limit
        if value < 1 or value > settings.sse_replay_limit:
            raise RealtimeEventsError("Event replay limit is outside the configured bound.")
        return value

    @staticmethod
    def _require_available() -> None:
        if not settings.realtime_events_enabled:
            raise RealtimeEventsError("Realtime event delivery is not enabled.")
        if settings.database_backend != "postgres":
            raise RealtimeEventsError("Realtime event delivery requires PostgreSQL and applied OAE migrations.")
