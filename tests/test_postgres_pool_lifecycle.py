from oae.api import db as db_module


def test_release_returns_postgres_connection_to_pool(monkeypatch):
    returned = []

    class FakePool:
        def putconn(self, connection):
            returned.append(connection)

    connection = object()
    db_module._POSTGRES_POOLS.clear()
    db_module._POSTGRES_POOLS["postgresql://example/test"] = FakePool()
    monkeypatch.setattr(db_module.settings, "database_url", "postgresql://example/test")

    adapter = db_module._ConnectionAdapter(connection, "postgres")
    db_module._release_connection(adapter)

    assert returned == [connection]
