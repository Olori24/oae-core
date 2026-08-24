"""PostgreSQL-backed rate limiting for horizontally scaled OAE API instances."""

from datetime import datetime, timezone

from oae.api.config import settings
from oae.api.db import db


class DistributedRateLimitExceeded(RuntimeError):
    """Raised when a shared rate-limit bucket is exhausted."""


def enforce_distributed_rate_limit(*, scope: str, subject: str, limit: int, window_seconds: int = 60) -> None:
    """Atomically consume one request from a shared PostgreSQL bucket.

    This is intentionally used for low-volume control-plane operations rather than every API
    request. PostgreSQL remains the source of truth and all API replicas observe the same bucket.
    """
    if limit <= 0 or settings.database_backend != "postgres":
        return

    bucket_key = f"{scope}:{subject}"
    now = datetime.now(timezone.utc)
    with db() as conn:
        row = conn.execute(
            """
            INSERT INTO api_rate_limit_buckets(bucket_key, window_started_at, request_count, updated_at)
            VALUES(?, ?, 1, ?)
            ON CONFLICT(bucket_key) DO UPDATE SET
                request_count = CASE
                    WHEN EXTRACT(EPOCH FROM (? - api_rate_limit_buckets.window_started_at)) >= ?
                    THEN 1
                    ELSE api_rate_limit_buckets.request_count + 1
                END,
                window_started_at = CASE
                    WHEN EXTRACT(EPOCH FROM (? - api_rate_limit_buckets.window_started_at)) >= ?
                    THEN ?
                    ELSE api_rate_limit_buckets.window_started_at
                END,
                updated_at = ?
            RETURNING request_count
            """,
            (bucket_key, now, now, now, window_seconds, now, window_seconds, now, now),
        ).fetchone()
    if row and int(row[0]) > limit:
        raise DistributedRateLimitExceeded("Control-plane rate limit exceeded. Retry after the current window.")
