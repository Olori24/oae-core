
import pytest

from oae.core.repository_update_engine import RepositoryUpdateEngine


def test_missing_repository(tmp_path):
    engine = RepositoryUpdateEngine()

    with pytest.raises(FileNotFoundError):
        engine.update(tmp_path / "missing")


def test_repository_exists(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    assert repo.exists()
