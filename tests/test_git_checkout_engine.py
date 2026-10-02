import subprocess

from oae.core.git_checkout_engine import GitCheckoutEngine


def _temporary_repository(tmp_path):
    repository = tmp_path / "repo"
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    return repository


def test_checkout_invalid_branch(tmp_path):
    engine = GitCheckoutEngine()
    repository = _temporary_repository(tmp_path)

    result = engine.checkout("branch_that_should_not_exist", cwd=repository)

    assert "returncode" in result
    assert "stdout" in result
    assert "stderr" in result
    assert result["branch"] == "branch_that_should_not_exist"
    assert result["returncode"] != 0


def test_create_branch_structure(tmp_path):
    engine = GitCheckoutEngine()
    repository = _temporary_repository(tmp_path)

    result = engine.create_and_checkout("oae-test", cwd=repository)

    assert "returncode" in result
    assert "stdout" in result
    assert "stderr" in result
    assert result["branch"] == "oae-test"
    assert result["returncode"] == 0
    current_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repository,
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()
    assert current_branch == "oae-test"
