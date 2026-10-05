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


def test_settings_default_to_an_empty_open_weight_model_allowlist():
    settings = Settings(open_weight_model_allowed_models="")

    assert settings.open_weight_model_allowed_models == []


def test_production_settings_reject_wildcard_security_defaults(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "*")
    monkeypatch.setenv("ALLOWED_HOSTS", "api.example.com")

    import pytest

    with pytest.raises(ValueError, match="CORS_ORIGINS"):
        Settings()


def test_production_settings_accept_explicit_security_origins(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "[\"https://app.example.com\"]")
    monkeypatch.setenv("ALLOWED_HOSTS", "[\"api.example.com\"]")
    monkeypatch.setenv("DATABASE_URL", "postgresql://example.test/oae")

    settings = Settings()

    assert settings.cors_origins == ["https://app.example.com"]
    assert settings.allowed_hosts == ["api.example.com"]
