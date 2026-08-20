"""Opt-in isolated PostgreSQL fixture support for durable queue end-to-end tests."""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

import pytest

from oae.api.config import settings
from oae.api.db import db
from oae.api.migrations import apply_postgres_migrations


def postgres_test_url() -> str | None:
    """Return the explicit integration database URL without exposing it in test output."""
    return os.getenv("OAE_POSTGRES_TEST_URL", "").strip() or None


def scoped_postgres_url(base_url: str, schema: str) -> str:
    parts = urlsplit(base_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["options"] = f"-c search_path={schema}"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


@pytest.fixture
def postgres_schema(monkeypatch) -> Iterator[str]:
    """Create a disposable schema, apply all tracked migrations, and point OAE at it."""
    base_url = postgres_test_url()
    if not base_url:
        pytest.skip("Set OAE_POSTGRES_TEST_URL to run PostgreSQL integration tests.")
    import psycopg
    from psycopg import sql

    schema = f"oae_it_{uuid4().hex}"
    with psycopg.connect(base_url, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    scoped_url = scoped_postgres_url(base_url, schema)
    monkeypatch.setattr(settings, "database_url", scoped_url)
    monkeypatch.setattr(settings, "realtime_events_enabled", True)
    monkeypatch.setattr(settings, "durable_jobs_enabled", True)
    monkeypatch.setattr(settings, "sse_poll_seconds", 0.01)
    monkeypatch.setattr(settings, "sse_heartbeat_seconds", 1)
    monkeypatch.setattr(settings, "sse_max_connection_seconds", 0.05)
    try:
        # The tracked migrations extend the base tenants, api_keys, and jobs tables.
        with db():
            pass
        with psycopg.connect(scoped_url) as connection:
            apply_postgres_migrations(connection)
        yield scoped_url
    finally:
        with psycopg.connect(base_url, autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@contextmanager
def postgres_connection(url: str):
    import psycopg

    with psycopg.connect(url) as connection:
        yield connection
