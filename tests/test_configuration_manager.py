import pytest

from oae.core.configuration_manager import ConfigurationManager


def test_generate(tmp_path):
    settings = ConfigurationManager().generate(tmp_path)
    content = settings.read_text()
    assert settings.exists()
    assert "APP_NAME" in content
    assert "DATABASE_URL" in content
    assert 'SECRET_KEY = os.environ["SECRET_KEY"]' in content
    assert "change-me" not in content


def test_generated_secret_requires_environment(tmp_path, monkeypatch):
    settings = ConfigurationManager().generate(tmp_path)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(KeyError):
        exec(settings.read_text(), {})
