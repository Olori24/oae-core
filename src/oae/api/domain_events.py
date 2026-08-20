"""Transaction-bound durable domain events for jobs, workspaces, and repositories."""

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

EVENT_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}\.[a-z][a-z0-9_]{0,63}$")
AGGREGATE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class DomainEventError(ValueError):
    """Raised when an externally visible event would violate the durable event contract."""


@dataclass(frozen=True)
class DomainEvent:
    id: str
    tenant_id: str
    tenant_sequence: int
    aggregate_type: str
    aggregate_id: str
    aggregate_sequence: int
    event_type: str
    payload: dict[str, Any]
    occurred_at: datetime
    correlation_id: str | None
    causation_id: str | None


class DomainEventWriter:
    """Appends ordered outbox records using the caller's active database transaction."""

    def append(
        self,
        conn,
        *,
        tenant_id: str,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, Any],
        correlation_id: str | None = None,
        causation_id: str | None = None,
        occurred_at: datetime | None = None,
    ) -> DomainEvent:
        self._validate(tenant_id, aggregate_type, aggregate_id, event_type, payload)
        timestamp = occurred_at or datetime.now(timezone.utc)
        tenant_sequence = int(
            conn.execute(
                """
                INSERT INTO tenant_event_cursors(tenant_id,last_sequence) VALUES(?,1)
                ON CONFLICT(tenant_id)
                DO UPDATE SET last_sequence=tenant_event_cursors.last_sequence+1
                RETURNING last_sequence
                """,
                (tenant_id,),
            ).fetchone()[0]
        )
        aggregate_sequence = int(
            conn.execute(
                """
                INSERT INTO aggregate_event_cursors(tenant_id,aggregate_type,aggregate_id,last_sequence)
                VALUES(?,?,?,1)
                ON CONFLICT(tenant_id,aggregate_type,aggregate_id)
                DO UPDATE SET last_sequence=aggregate_event_cursors.last_sequence+1
                RETURNING last_sequence
                """,
                (tenant_id, aggregate_type, aggregate_id),
            ).fetchone()[0]
        )
        event_id = str(uuid4())
        conn.execute(
            """
            INSERT INTO outbox_events(
                id,tenant_id,aggregate_type,aggregate_id,event_type,payload,occurred_at,
                published_at,publish_attempts,next_publish_at,tenant_sequence,aggregate_sequence,
                correlation_id,causation_id,relay_lease_token,relay_lease_expires_at,last_error_redacted
            ) VALUES(?,?,?,?,?,?::jsonb,?,NULL,0,?,?,?,?,?,NULL,NULL,NULL)
            """,
            (
                event_id,
                tenant_id,
                aggregate_type,
                aggregate_id,
                event_type,
                json.dumps(payload, separators=(",", ":"), sort_keys=True),
                timestamp,
                timestamp,
                tenant_sequence,
                aggregate_sequence,
                correlation_id,
                causation_id,
            ),
        )
        return DomainEvent(
            id=event_id,
            tenant_id=tenant_id,
            tenant_sequence=tenant_sequence,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            aggregate_sequence=aggregate_sequence,
            event_type=event_type,
            payload=payload,
            occurred_at=timestamp,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    @staticmethod
    def _validate(
        tenant_id: str,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        if not tenant_id or not aggregate_id:
            raise DomainEventError("Tenant and aggregate identifiers are required.")
        if not AGGREGATE_NAME_PATTERN.fullmatch(aggregate_type):
            raise DomainEventError("Aggregate type must be a lowercase identifier.")
        if not EVENT_NAME_PATTERN.fullmatch(event_type):
            raise DomainEventError("Event type must use aggregate.action notation.")
        if not isinstance(payload, dict):
            raise DomainEventError("Event payload must be an object.")
        try:
            encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        except (TypeError, ValueError) as exc:
            raise DomainEventError("Event payload must be JSON serializable.") from exc
        if len(encoded.encode("utf-8")) > 32 * 1024:
            raise DomainEventError("Event payload exceeds the 32 KiB durable-event limit.")
