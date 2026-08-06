from pathlib import Path

from oae.core.repository_worktree_manager import (
    RepositoryWorktreeManager,
)


def test_create_worktree():
    manager = RepositoryWorktreeManager()

    result = manager.create_worktree()

    assert result["created"] is True
    assert Path(result["path"]).exists()


def test_remove_worktree():
    manager = RepositoryWorktreeManager()

    worktree = manager.create_worktree()

    result = manager.remove_worktree(worktree["path"])

    assert result["removed"] is True
    assert not Path(worktree["path"]).exists()


def test_remove_missing_worktree():
    manager = RepositoryWorktreeManager()

    result = manager.remove_worktree("/tmp/oae_missing_worktree")

    assert result["removed"] is True
