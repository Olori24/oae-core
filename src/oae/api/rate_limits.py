"""Shared database-backed control-plane rate limiting."""

import time

from oae.api.db import db


class RateLimitExceeded(RuntimeError):
    """Raised when a principal or origin exceeds its control-plane budget."""


class DatabaseRateLimiter:
    def enforce(self, *, scope: str, subject: str, limit: int, window_seconds: int = 60) -> None:
        if limit <= 0:
            return
        if window_seconds < 1:
            raise ValueError("window_seconds must be positive")
        now = int(time.time())
        window_start = now - (now % window_seconds)
        with db() as conn:
            row = conn.execute(
                """
                INSERT INTO rate_limit_buckets(scope,subject,window_start,hit_count)
                VALUES(?,?,?,1)
                ON CONFLICT(scope,subject,window_start)
                DO UPDATE SET hit_count=rate_limit_buckets.hit_count+1
                RETURNING hit_count
                """,
                (scope, subject, window_start),
            ).fetchone()
            if row and int(row[0]) > limit:
                raise RateLimitExceeded("Control-plane rate limit exceeded. Retry after the current window.")
            conn.execute(
                "DELETE FROM rate_limit_buckets WHERE window_start < ?",
                (window_start - (window_seconds * 2),),
            )


rate_limiter = DatabaseRateLimiter()
