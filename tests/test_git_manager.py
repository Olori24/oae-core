from oae.git import GitManager


def test_git_manager_creation():
    manager = GitManager()

    assert manager is not None


def test_current_branch_returns_string():
    manager = GitManager()

    assert isinstance(manager.current_branch(), str)


def test_status_returns_string():
    manager = GitManager()

    assert isinstance(manager.status(), str)