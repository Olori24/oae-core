from pathlib import Path

from oae.core.repository_clone_engine import RepositoryCloneEngine


def test_clone(tmp_path):
    source = tmp_path / "repo"
    source.mkdir()

    (source / "main.py").write_text("print('hello')")

    destination = tmp_path / "clone"

    engine = RepositoryCloneEngine()

    result = engine.clone(source, destination)

    assert result["status"] == "cloned"
    assert destination.exists()
    assert (destination / "main.py").exists()


def test_clone_contents(tmp_path):
    source = tmp_path / "repo"
    source.mkdir()

    (source / "app.py").write_text("print('app')")

    destination = tmp_path / "copy"

    engine = RepositoryCloneEngine()

    engine.clone(source, destination)

    assert (destination / "app.py").read_text() == "print('app')"
