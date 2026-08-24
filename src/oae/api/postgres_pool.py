"""Process-local bounded PostgreSQL connection pool.

The pool is deliberately bounded per process. Deployment sizing must account for
API, worker, relay, and migration processes against the database connection budget.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Iterator

from oae.api.config import settings

_pool = None
_pool_url = ""
_pool_lock = threading.Lock()


def _get_pool():
    global _pool, _pool_url
    if _pool is not None and _pool_url == settings.resolved_database_url:
        return _pool
    with _pool_lock:
        if _pool is not None and _pool_url == settings.resolved_database_url:
            return _pool
        try:
            from psycopg_pool import ConnectionPool
        except ImportError as exc:
            raise RuntimeError("Postgres is configured but psycopg-pool is not installed") from exc

        if settings.postgres_pool_min_size > settings.postgres_pool_max_size:
            raise RuntimeError("POSTGRES_POOL_MIN_SIZE cannot exceed POSTGRES_POOL_MAX_SIZE")

        if _pool is not None:
            _pool.close()

        _pool = ConnectionPool(
            conninfo=settings.resolved_database_url,
            min_size=settings.postgres_pool_min_size,
            max_size=settings.postgres_pool_max_size,
            timeout=settings.postgres_pool_timeout_seconds,
            max_lifetime=settings.postgres_pool_max_lifetime_seconds,
            open=False,
        )
        _pool.open(wait=True, timeout=settings.postgres_pool_timeout_seconds)
        _pool_url = settings.resolved_database_url
        return _pool


@contextmanager
def connection() -> Iterator:
    """Borrow one connection and always return it to the bounded pool."""
    pool = _get_pool()
    with pool.connection() as conn:
        yield conn


def close_pool() -> None:
    global _pool, _pool_url
    with _pool_lock:
        if _pool is not None:
            _pool.close()
            _pool = None
            _pool_url = ""
