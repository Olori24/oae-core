from types import SimpleNamespace

import pytest

from oae.api import distributed_rate_limits


class FakeCursor:
    def __init__(self, count):
        self.count = count

    def execute(self, *_args, **_kwargs):
        return None

    def fetchone(self):
        return (self.count,)


class FakeConnection:
    def __init__(self, count):
        self.cursor_obj = FakeCursor(count)

    def execute(self, *_args, **_kwargs):
        return self.cursor_obj


class FakeContext:
    def __init__(self, count):
        self.connection = FakeConnection(count)

    def __enter__(self):
        return self.connection

    def __exit__(self, *_args):
        return False


def test_distributed_limiter_allows_request(monkeypatch):
    monkeypatch.setattr(
        distributed_rate_limits,
        "settings",
        SimpleNamespace(database_backend="postgres"),
    )
    monkeypatch.setattr(distributed_rate_limits, "db", lambda: FakeContext(1))

    distributed_rate_limits.enforce_distributed_rate_limit(
        scope="test", subject="tenant-a", limit=2
    )


def test_distributed_limiter_rejects_exhausted_bucket(monkeypatch):
    monkeypatch.setattr(
        distributed_rate_limits,
        "settings",
        SimpleNamespace(database_backend="postgres"),
    )
    monkeypatch.setattr(distributed_rate_limits, "db", lambda: FakeContext(3))

    with pytest.raises(distributed_rate_limits.DistributedRateLimitExceeded):
        distributed_rate_limits.enforce_distributed_rate_limit(
            scope="test", subject="tenant-a", limit=2
        )


def test_distributed_limiter_is_noop_without_postgres(monkeypatch):
    monkeypatch.setattr(
        distributed_rate_limits,
        "settings",
        SimpleNamespace(database_backend="sqlite"),
    )
    distributed_rate_limits.enforce_distributed_rate_limit(
        scope="test", subject="tenant-a", limit=1
    )
