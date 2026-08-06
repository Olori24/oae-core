from oae.core.git_branch_manager import GitBranchManager


def test_create_branch():
    manager = GitBranchManager()

    result = manager.create_branch("oae/test")

    assert result["status"] == "created"
    assert result["branch"] == "oae/test"


def test_checkout():
    manager = GitBranchManager()

    result = manager.checkout("oae/test")

    assert result["status"] == "checked_out"


def test_current_branch():
    manager = GitBranchManager()

    assert manager.current_branch() == "main"


def test_delete_branch():
    manager = GitBranchManager()

    result = manager.delete_branch("oae/test")

    assert result["status"] == "deleted"
