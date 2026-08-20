
from oae.core.repository_scanner import RepositoryScanner


def test_creation():
    scanner = RepositoryScanner()

    assert scanner is not None


def test_scan(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    app = repo / "app.py"
    app.write_text("print('hello')")

    scanner = RepositoryScanner()

    files = scanner.scan(repo)

    assert "app.py" in files


def test_ignore_git(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    git = repo / ".git"
    git.mkdir()

    hidden = git / "ignored.py"
    hidden.write_text("print('ignore')")

    scanner = RepositoryScanner()

    files = scanner.scan(repo)

    assert files == {}


def test_multiple_files(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    (repo / "a.py").write_text("A")
    (repo / "b.py").write_text("B")

    scanner = RepositoryScanner()

    files = scanner.scan(repo)

    assert len(files) == 2


def test_nested_directory(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    src = repo / "src"
    src.mkdir()

    (src / "main.py").write_text("print('ok')")

    scanner = RepositoryScanner()

    files = scanner.scan(repo)

    assert "src/main.py" in files