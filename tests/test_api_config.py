from oae.api.config import Settings


def test_oae_db_url_is_supported(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("POSTGRES_PRISMA_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL_NON_POOLING", raising=False)
    monkeypatch.delenv("OAE_DB", raising=False)
    monkeypatch.setenv("OAE_DB_URL", "postgresql://example.test/oae")

    settings = Settings()

    assert settings.resolved_database_url == "postgresql://example.test/oae"
    assert settings.database_backend == "postgres"


def test_oae_db_alias_is_supported(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("OAE_DB_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("POSTGRES_PRISMA_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL_NON_POOLING", raising=False)
    monkeypatch.setenv("OAE_DB", "postgresql://example.test/oae")

    settings = Settings()

    assert settings.resolved_database_url == "postgresql://example.test/oae"
    assert settings.database_backend == "postgres"
