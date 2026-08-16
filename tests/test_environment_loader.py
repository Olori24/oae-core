from oae.core.environment_loader import EnvironmentLoader


def test_load_environment(tmp_path):
    env = tmp_path / ".env"

    env.write_text(
        """APP_NAME=OAE
DATABASE_URL=sqlite:///app.db
DEBUG=True
"""
    )

    loader = EnvironmentLoader()

    values = loader.load(tmp_path)

    assert values["APP_NAME"] == "OAE"
    assert values["DATABASE_URL"] == "sqlite:///app.db"
    assert values["DEBUG"] == "True"


def test_missing_env_file(tmp_path):
    loader = EnvironmentLoader()

    values = loader.load(tmp_path)

    assert values == {}
