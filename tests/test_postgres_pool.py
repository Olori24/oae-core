import threading
import time

from oae.api import postgres_pool


class _FakeConnection:
    def __init__(self):
        self.closed = False
        self.rollbacks = 0

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def test_pool_never_exceeds_maximum(monkeypatch):
    monkeypatch.setattr(postgres_pool.settings, "postgres_pool_min_size", 1)
    monkeypatch.setattr(postgres_pool.settings, "postgres_pool_max_size", 2)
    monkeypatch.setattr(postgres_pool.settings, "postgres_pool_timeout_seconds", 0.05)
    pool = postgres_pool.PostgresConnectionPool("postgresql://test")
    monkeypatch.setattr(pool, "_new_connection", _FakeConnection)

    pool.warm()
    first = pool.acquire()
    second = pool.acquire()

    assert pool.metrics()["total"] == 2
    assert pool.metrics()["active"] == 2

    errors = []

    def blocked_acquire():
        try:
            pool.acquire()
        except RuntimeError as exc:
            errors.append(str(exc))

    thread = threading.Thread(target=blocked_acquire)
    thread.start()
    thread.join(timeout=1)

    assert errors == ["Postgres connection pool exhausted"]
    pool.release(first)
    pool.release(second)
    assert pool.metrics()["idle"] == 2
    pool.close()


def test_pool_reuses_connection_and_rolls_back_before_return(monkeypatch):
    monkeypatch.setattr(postgres_pool.settings, "postgres_pool_min_size", 0)
    monkeypatch.setattr(postgres_pool.settings, "postgres_pool_max_size", 1)
    pool = postgres_pool.PostgresConnectionPool("postgresql://test")
    monkeypatch.setattr(pool, "_new_connection", _FakeConnection)

    first = pool.acquire()
    pool.release(first)
    second = pool.acquire()

    assert second is first
    assert first.rollbacks == 1
    pool.close()
    assert first.closed is True
