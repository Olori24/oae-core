from contextlib import contextmanager

from oae.api import auth


class _FakeConn:
    def __init__(self, rows):
        self.rows = rows
        self.calls = 0

    def execute(self, query, params=()):
        self.calls += 1
        return self

    def fetchall(self):
        return self.rows



def test_authentication_cache_avoids_repeated_pbkdf2_lookup(monkeypatch):
    raw = "oae_test_cache_key"
    stored = auth.hash_key(raw)
    row = ("key-1", "tenant-1", stored, "principal-1", "owner")
    fake = _FakeConn([row])

    @contextmanager
    def fake_db():
        yield fake

    monkeypatch.setattr(auth, "db", fake_db)
    monkeypatch.setattr(auth.settings, "auth_cache_ttl_seconds", 10.0)
    monkeypatch.setattr(auth.settings, "auth_cache_max_entries", 100)
    with auth._AUTH_CACHE_LOCK:
        auth._AUTH_CACHE.clear()

    first = auth.require_principal(f"Bearer {raw}")
    calls_after_first = fake.calls
    second = auth.require_principal(f"Bearer {raw}")

    assert first == second
    assert calls_after_first == 1
    assert fake.calls == calls_after_first
    assert auth.auth_cache_metrics()["hits"] >= 1


def test_revocation_invalidates_cached_principal(monkeypatch):
    raw = "oae_test_revoke_key"
    principal = auth.TenantPrincipal("tenant-1", "key-2", "principal-2", "owner")
    auth._cache_put(raw, principal)

    auth._cache_invalidate_key("key-2")

    assert auth._cache_get(raw) is None
