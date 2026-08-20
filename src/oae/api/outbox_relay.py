"""Durable PostgreSQL relay that projects transactional outbox rows into replayable events."""

import argparse
import json
import logging
import socket
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from oae.api.config import settings
from oae.api.db import db

logger = logging.getLogger("oae.api.outbox_relay")


class OutboxRelayError(RuntimeError):
    """Base error for transactional outbox projection failures."""


@dataclass(frozen=True)
class OutboxEvent:
    id: str
    tenant_id: str
    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: dict[str, Any]
    occurred_at: datetime
    tenant_sequence: int
    aggregate_sequence: int
    correlation_id: str | None
    causation_id: str | None
    lease_token: str


@dataclass(frozen=True)
class RelayRunResult:
    claimed: int
    projected: int
    blocked: int
    failed: int


class OutboxRelay:
    """Projects committed outbox records while preserving monotonic tenant replay order."""

    def __init__(self, relay_id: str | None = None):
        self.relay_id = relay_id or f"{socket.gethostname()}-relay"

    def run_once(self, batch_size: int | None = None) -> RelayRunResult:
        self._require_postgres()
        events = self.claim_batch(batch_size or settings.outbox_relay_batch_size)
        projected = blocked = failed = 0
        for event in events:
            try:
                if self.project(event):
                    projected += 1
                else:
                    blocked += 1
            except Exception as exc:
                failed += 1
                logger.exception("outbox_projection_failed event_id=%s", event.id)
                self.record_failure(event, exc)
        return RelayRunResult(len(events), projected, blocked, failed)

    def claim_batch(self, batch_size: int) -> list[OutboxEvent]:
        self._require_postgres()
        if batch_size < 1 or batch_size > 500:
            raise OutboxRelayError("Relay batch size must be between 1 and 500.")
        token = str(uuid4())
        with db() as conn:
            rows = conn.execute(
                """
                WITH candidates AS (
                    SELECT id FROM outbox_events
                    WHERE published_at IS NULL
                      AND tenant_sequence IS NOT NULL
                      AND next_publish_at <= now()
                      AND (relay_lease_expires_at IS NULL OR relay_lease_expires_at < now())
                    ORDER BY occurred_at ASC, id ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT ?
                )
                UPDATE outbox_events AS event
                SET relay_lease_token=?, relay_lease_expires_at=now() + (? * interval '1 second'),
                    publish_attempts=event.publish_attempts+1
                FROM candidates
                WHERE event.id=candidates.id
                RETURNING event.id,event.tenant_id,event.aggregate_type,event.aggregate_id,event.event_type,
                    event.payload,event.occurred_at,event.tenant_sequence,event.aggregate_sequence,
                    event.correlation_id,event.causation_id,event.relay_lease_token
                """,
                (batch_size, token, settings.outbox_relay_lease_seconds),
            ).fetchall()
        return [self._event(row) for row in rows]

    def project(self, event: OutboxEvent) -> bool:
        """Project one leased event; return False when an earlier tenant event still fences it."""
        self._require_postgres()
        with db() as conn:
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(?, 0))", (event.tenant_id,))
            current = conn.execute(
                """
                SELECT id,tenant_sequence FROM outbox_events
                WHERE id=? AND tenant_id=? AND published_at IS NULL AND relay_lease_token=?
                    AND relay_lease_expires_at > now()
                FOR UPDATE
                """,
                (event.id, event.tenant_id, event.lease_token),
            ).fetchone()
            if not current:
                return False
            cursor = conn.execute(
                """
                INSERT INTO tenant_event_publication_cursors(tenant_id,last_published_sequence)
                VALUES(?,0)
                ON CONFLICT(tenant_id) DO UPDATE
                SET last_published_sequence=tenant_event_publication_cursors.last_published_sequence
                RETURNING last_published_sequence
                """,
                (event.tenant_id,),
            ).fetchone()
            expected = int(cursor[0]) + 1
            if event.tenant_sequence != expected:
                conn.execute(
                    """
                    UPDATE outbox_events
                    SET relay_lease_token=NULL,relay_lease_expires_at=NULL,
                        next_publish_at=now() + interval '1 second'
                    WHERE id=? AND relay_lease_token=? AND published_at IS NULL
                    """,
                    (event.id, event.lease_token),
                )
                return False
            conn.execute(
                """
                INSERT INTO realtime_events(
                    id,outbox_event_id,tenant_id,tenant_sequence,aggregate_type,aggregate_id,
                    aggregate_sequence,event_type,payload,occurred_at,correlation_id,causation_id
                ) VALUES(?,?,?,?,?,?,?, ?, ?::jsonb,?,?,?)
                ON CONFLICT(outbox_event_id) DO NOTHING
                """,
                (
                    event.id,
                    event.id,
                    event.tenant_id,
                    event.tenant_sequence,
                    event.aggregate_type,
                    event.aggregate_id,
                    event.aggregate_sequence,
                    event.event_type,
                    json.dumps(event.payload, separators=(",", ":"), sort_keys=True),
                    event.occurred_at,
                    event.correlation_id,
                    event.causation_id,
                ),
            )
            if event.aggregate_type == "job":
                conn.execute(
                    """
                    INSERT INTO job_events(id,tenant_id,job_id,sequence,event_type,payload,created_at)
                    VALUES(?,?,?,?,?,?::jsonb,?)
                    ON CONFLICT(id) DO NOTHING
                    """,
                    (
                        event.id,
                        event.tenant_id,
                        event.aggregate_id,
                        event.aggregate_sequence,
                        event.event_type,
                        json.dumps(event.payload, separators=(",", ":"), sort_keys=True),
                        event.occurred_at,
                    ),
                )
            conn.execute(
                """
                UPDATE tenant_event_publication_cursors
                SET last_published_sequence=?
                WHERE tenant_id=? AND last_published_sequence=?
                """,
                (event.tenant_sequence, event.tenant_id, expected - 1),
            )
            changed = conn.execute(
                """
                UPDATE outbox_events
                SET published_at=now(),relay_lease_token=NULL,relay_lease_expires_at=NULL,
                    last_error_redacted=NULL
                WHERE id=? AND tenant_id=? AND relay_lease_token=? AND published_at IS NULL
                """,
                (event.id, event.tenant_id, event.lease_token),
            ).rowcount
        if changed != 1:
            raise OutboxRelayError("Relay projection lost ownership before publication acknowledgement.")
        return True

    def record_failure(self, event: OutboxEvent, exc: Exception) -> None:
        """Release a failed lease with bounded redacted context and deterministic retry delay."""
        self._require_postgres()
        redacted = f"{exc.__class__.__name__}: projection_failed"
        with db() as conn:
            row = conn.execute(
                "SELECT publish_attempts FROM outbox_events WHERE id=? AND relay_lease_token=? FOR UPDATE",
                (event.id, event.lease_token),
            ).fetchone()
            if not row:
                return
            delay = min(settings.outbox_relay_retry_max_seconds, 2 ** max(int(row[0]) - 1, 0))
            conn.execute(
                """
                UPDATE outbox_events
                SET relay_lease_token=NULL,relay_lease_expires_at=NULL,last_error_redacted=?,
                    next_publish_at=now() + (? * interval '1 second')
                WHERE id=? AND relay_lease_token=? AND published_at IS NULL
                """,
                (redacted, delay, event.id, event.lease_token),
            )

    @staticmethod
    def _event(row) -> OutboxEvent:
        payload = row[5]
        if isinstance(payload, str):
            payload = json.loads(payload)
        occurred_at = row[6]
        if isinstance(occurred_at, str):
            occurred_at = datetime.fromisoformat(occurred_at)
        return OutboxEvent(
            id=str(row[0]),
            tenant_id=str(row[1]),
            aggregate_type=str(row[2]),
            aggregate_id=str(row[3]),
            event_type=str(row[4]),
            payload=payload,
            occurred_at=occurred_at,
            tenant_sequence=int(row[7]),
            aggregate_sequence=int(row[8]),
            correlation_id=row[9],
            causation_id=row[10],
            lease_token=str(row[11]),
        )

    @staticmethod
    def _require_postgres() -> None:
        if settings.database_backend != "postgres":
            raise OutboxRelayError("Transactional outbox relay requires PostgreSQL and applied OAE migrations.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the OAE transactional outbox relay.")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    parser.add_argument("--batch-size", type=int, default=settings.outbox_relay_batch_size)
    args = parser.parse_args()
    relay = OutboxRelay()
    while True:
        result = relay.run_once(args.batch_size)
        if args.once:
            return 0
        if result.claimed == 0:
            time.sleep(max(args.poll_seconds, 0.1))
