from pathlib import Path

import pytest

from oae.core.repository_worktree import RepositoryWorktree, WorktreeError


def test_worktree_mutation_diff_and_commit(tmp_path: Path):
    (tmp_path / "README.md").write_text("hello\n", encoding="utf-8")
    wt = RepositoryWorktree(tmp_path)
    from oae.core.process_security import run_git
    run_git(["init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    run_git(["add", "README.md"], cwd=tmp_path, check=True, capture_output=True, text=True)
    run_git(
        ["-c", "user.name=seed", "-c", "user.email=seed@example.invalid", "commit", "-m", "seed"],
        cwd=tmp_path, check=True, capture_output=True, text=True,
    )
    wt.create_branch("oae/task-1")
    wt.write_file("src/app.py", "print('ok')\n")
    diff = wt.diff()
    assert "src/app.py" in diff["diff"]
    committed = wt.commit("feat: add app")
    assert committed["branch"] == "oae/task-1"
    assert len(committed["commit_sha"]) == 40
    assert wt.status()["entries"] == []


def test_worktree_blocks_traversal_and_git_mutation(tmp_path: Path):
    wt = RepositoryWorktree(tmp_path)
    with pytest.raises(WorktreeError):
        wt.write_file("../escape.txt", "x")
    with pytest.raises(WorktreeError):
        wt.write_file(".git/config", "x")


def test_branch_validation(tmp_path: Path):
    wt = RepositoryWorktree(tmp_path)
    from oae.core.process_security import run_git
    run_git(["init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    with pytest.raises(WorktreeError):
        wt.create_branch("../bad")
