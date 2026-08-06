from oae.core.git_operations import GitOperations


def test_status():
    git = GitOperations()

    result = git.status()

    assert "returncode" in result
    assert "stdout" in result
    assert "stderr" in result


def test_current_branch():
    git = GitOperations()

    branch = git.current_branch()

    assert isinstance(branch, str)


def test_run():
    git = GitOperations()

    result = git.run("--version")

    assert result["returncode"] == 0
    assert "git version" in result["stdout"]
