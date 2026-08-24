"""Small process-local PostgreSQL connection pool with bounded concurrency."""

from __future__ import annotations

import queue
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from oae.api.config import settings


@dataclass
class _PooledConnection:
    connection: object
    created_at: float


class PostgresConnectionPool:
    def __init__(self, database_url: str):
        if settings.postgres_pool_min_size > settings.postgres_pool_max_size:
            raise RuntimeError("POSTGRES_POOL_MIN_SIZE cannot exceed POSTGRES_POOL_MAX_SIZE")
        self.database_url = database_url
        self.min_size = settings.postgres_pool_min_size
        self.max_size = settings.postgres_pool_max_size
        self.timeout = settings.postgres_pool_timeout_seconds
        self.max_lifetime = settings.postgres_pool_max_lifetime_seconds
        self._idle: queue.LifoQueue[_PooledConnection] = queue.LifoQueue(maxsize=self.max_size)
        self._condition = threading.Condition()
        self._births: dict[int, float] = {}
        self._total = 0
        self._closed = False
        self._waiters = 0
        self._wait_count = 0
        self._wait_seconds = 0.0
        self._created = 0

    def _new_connection(self):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("Postgres is configured but psycopg is not installed") from exc
        conn = psycopg.connect(self.database_url, connect_timeout=max(1, int(self.timeout)))
        created_at = time.monotonic()
        self._births[id(conn)] = created_at
        self._created += 1
        return conn

    def _expired(self, item: _PooledConnection) -> bool:
        return time.monotonic() - item.created_at >= self.max_lifetime

    def acquire(self):
        started = time.monotonic()
        deadline = started + self.timeout
        with self._condition:
            while True:
                if self._closed:
                    raise RuntimeError("Postgres connection pool is closed")
                try:
                    item = self._idle.get_nowait()
                except queue.Empty:
                    item = None
                if item is not None:
                    if self._expired(item):
                        try:
                            item.connection.close()
                        finally:
                            self._births.pop(id(item.connection), None)
                            self._total -= 1
                        continue
                    return item.connection
                if self._total < self.max_size:
                    self._total += 1
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self._wait_count += 1
                    self._wait_seconds += time.monotonic() - started
                    raise RuntimeError("Postgres connection pool exhausted")
                self._waiters += 1
                try:
                    self._condition.wait(timeout=remaining)
                finally:
                    self._waiters -= 1
            self._wait_count += 1
            self._wait_seconds += time.monotonic() - started

        try:
            return self._new_connection()
        except Exception:
            with self._condition:
                self._total -= 1
                self._condition.notify()
            raise

    def release(self, connection) -> None:
        try:
            connection.rollback()
        except Exception:
            try:
                connection.close()
            finally:
                with self._condition:
                    self._births.pop(id(connection), None)
                    self._total -= 1
                    self._condition.notify()
            return

        created_at = self._births.get(id(connection), time.monotonic())
        item = _PooledConnection(connection, created_at)
        with self._condition:
            if self._closed or self._expired(item):
                try:
                    connection.close()
                finally:
                    self._births.pop(id(connection), None)
                    self._total -= 1
                    self._condition.notify()
                return
            self._idle.put_nowait(item)
            self._condition.notify()

    def close(self) -> None:
        with self._condition:
            self._closed = True
            while True:
                try:
                    item = self._idle.get_nowait()
                except queue.Empty:
                    break
                try:
                    item.connection.close()
                finally:
                    self._births.pop(id(item.connection), None)
                    self._total -= 1
            self._condition.notify_all()

    def metrics(self) -> dict[str, int | float]:
        with self._condition:
            idle = self._idle.qsize()
            return {
                "total": self._total,
                "idle": idle,
                "active": max(0, self._total - idle),
                "max": self.max_size,
                "waiters": self._waiters,
                "wait_count": self._wait_count,
                "wait_seconds": round(self._wait_seconds, 6),
                "created": self._created,
            }


_pool: PostgresConnectionPool | None = None
_pool_url = ""
_pool_lock = threading.Lock()


def _get_pool() -> PostgresConnectionPool:
    global _pool, _pool_url
    url = settings.resolved_database_url
    if _pool is not None and _pool_url == url:
        return _pool
    with _pool_lock:
        if _pool is not None and _pool_url == url:
            return _pool
        if _pool is not None:
            _pool.close()
        _pool = PostgresConnectionPool(url)
        _pool_url = url
        return _pool


@contextmanager
def connection() -> Iterator:
    pool = _get_pool()
    conn = pool.acquire()
    try:
        yield conn
    finally:
        pool.release(conn)


def pool_metrics() -> dict[str, int | float]:
    return _get_pool().metrics()


def close_pool() -> None:
    global _pool, _pool_url
    with _pool_lock:
        if _pool is not None:
            _pool.close()
            _pool = None
            _pool_url = ""
