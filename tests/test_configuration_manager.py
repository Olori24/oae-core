from oae.core.configuration_manager import ConfigurationManager


def test_generate(tmp_path):
    manager = ConfigurationManager()

    settings = manager.generate(tmp_path)

    assert settings.exists()
    assert "APP_NAME" in settings.read_text()
    assert "DATABASE_URL" in settings.read_text()
