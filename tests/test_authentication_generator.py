import pytest

from oae.core.authentication_generator import AuthenticationGenerator


def test_generate(tmp_path):
    AuthenticationGenerator().generate(tmp_path)

    assert (tmp_path / "src" / "auth" / "security.py").exists()
    assert (tmp_path / "src" / "models" / "user.py").exists()
    assert (tmp_path / "src" / "api" / "auth.py").exists()


def test_generated_security_requires_secret_key(tmp_path, monkeypatch):
    AuthenticationGenerator().generate(tmp_path)
    security = tmp_path / "src" / "auth" / "security.py"
    monkeypatch.delenv("SECRET_KEY", raising=False)

    assert "change-me" not in security.read_text()
    with pytest.raises(ValueError, match="SECRET_KEY must be set"):
        exec(security.read_text(), {})
