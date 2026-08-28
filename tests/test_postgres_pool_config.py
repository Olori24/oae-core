from types import SimpleNamespace
import sys

from oae.api import db as db_module


def test_postgres_pool_uses_bounded_configuration(monkeypatch):
    created = {}

    class FakePool:
        def __init__(self, **kwargs):
            created.update(kwargs)

    monkeypatch.setitem(sys.modules, 'psycopg_pool', SimpleNamespace(ConnectionPool=FakePool))
    settings = db_module.settings
    monkeypatch.setattr(settings, 'database_backend', 'postgres')
    monkeypatch.setattr(settings, 'resolved_database_url', 'postgresql://example/test')
    monkeypatch.setattr(settings, 'postgres_pool_min_size', 2, raising=False)
    monkeypatch.setattr(settings, 'postgres_pool_max_size', 8, raising=False)
    monkeypatch.setattr(settings, 'postgres_pool_timeout', 3.0, raising=False)
    db_module._POSTGRES_POOLS.clear()

    pool = db_module._postgres_pool()

    assert pool is db_module._POSTGRES_POOLS['postgresql://example/test']
    assert created == {'conninfo': 'postgresql://example/test', 'min_size': 2, 'max_size': 8, 'timeout': 3.0, 'open': True}
