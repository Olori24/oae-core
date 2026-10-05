"""Governed Git worktree operations for mutable engineering workspaces.

The workspace filesystem is disposable. This controller makes the Git boundary
explicit: paths are relative to the workspace, branch names are validated, and
only the workspace's own repository is modified.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from oae.core.process_security import run_git, validate_git_ref

_SAFE_BRANCH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,119}$")
_MAX_FILE_BYTES = 2 * 1024 * 1024
_MAX_DIFF_BYTES = 200_000


class WorktreeError(RuntimeError):
    """Raised when a governed worktree operation cannot be completed."""


class RepositoryWorktree:
    """Attach a disposable workspace to a pinned Git revision and manage changes."""

    def __init__(self, workspace: str | Path):
        self.root = Path(workspace).expanduser().resolve()
        if not self.root.is_dir():
            raise WorktreeError("workspace directory does not exist")

    def attach(self, *, clone_url: str, commit_sha: str) -> dict[str, str]:
        if (self.root / ".git").exists():
            return {"status": "attached", "commit_sha": self.head()}
        validate_git_ref(commit_sha)
        run_git(["init"], cwd=self.root, check=True, capture_output=True, text=True)
        run_git(
            ["remote", "add", "origin", clone_url],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        run_git(
            ["fetch", "--depth", "1", "origin", commit_sha],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        run_git(
            ["reset", "--hard", commit_sha],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        return {"status": "attached", "commit_sha": self.head()}

    def create_branch(self, name: str) -> dict[str, str]:
        self._require_repo()
        self._validate_branch(name)
        run_git(["switch", "-c", name], cwd=self.root, check=True, capture_output=True, text=True)
        return {"branch": self.branch(), "commit_sha": self.head()}

    def write_file(self, relative_path: str, content: str) -> dict[str, Any]:
        path = self._safe_path(relative_path)
        encoded = content.encode("utf-8")
        if len(encoded) > _MAX_FILE_BYTES:
            raise WorktreeError("file exceeds the governed mutation limit")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded)
        return {"path": relative_path, "size_bytes": len(encoded)}

    def delete_file(self, relative_path: str) -> dict[str, str]:
        path = self._safe_path(relative_path)
        if not path.is_file():
            raise WorktreeError("file does not exist")
        path.unlink()
        return {"path": relative_path, "status": "deleted"}

    def status(self) -> dict[str, Any]:
        self._require_repo()
        result = run_git(
            ["status", "--porcelain=v1", "--branch"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        return {
            "branch": self.branch(),
            "commit_sha": self.head(),
            "entries": [line for line in result.stdout.splitlines() if line and not line.startswith("## ")],
        }

    def diff(self) -> dict[str, Any]:
        self._require_repo()
        result = run_git(
            ["diff", "--no-ext-diff", "--binary"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        encoded = result.stdout.encode("utf-8")
        if len(encoded) > _MAX_DIFF_BYTES:
            raise WorktreeError("diff exceeds the governed evidence limit")
        return {"branch": self.branch(), "commit_sha": self.head(), "diff": result.stdout}

    def commit(self, message: str) -> dict[str, str]:
        self._require_repo()
        message = message.strip()
        if not message or len(message) > 200:
            raise WorktreeError("commit message must be between 1 and 200 characters")
        status = self.status()
        if not status["entries"]:
            raise WorktreeError("cannot commit a clean worktree")
        run_git(["add", "--all"], cwd=self.root, check=True, capture_output=True, text=True)
        run_git(
            ["-c", "user.name=OAE Core", "-c", "user.email=engineering@oae.invalid",
             "commit", "-m", message],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        return {"branch": self.branch(), "commit_sha": self.head(), "message": message}

    def head(self) -> str:
        self._require_repo()
        return run_git(["rev-parse", "HEAD"], cwd=self.root, check=True, capture_output=True, text=True).stdout.strip()

    def branch(self) -> str:
        self._require_repo()
        return run_git(["branch", "--show-current"], cwd=self.root, check=True, capture_output=True, text=True).stdout.strip()

    def _safe_path(self, relative_path: str) -> Path:
        candidate = Path(relative_path)
        if (
            not relative_path
            or candidate.is_absolute()
            or ".." in candidate.parts
            or candidate.parts[:1] == (".git",)
        ):
            raise WorktreeError("path must remain inside the workspace and cannot target .git")
        resolved = (self.root / candidate).resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise WorktreeError("path escapes the workspace") from exc
        return resolved

    def _require_repo(self) -> None:
        if not (self.root / ".git").exists():
            raise WorktreeError("workspace is not attached to a Git worktree")

    @staticmethod
    def _validate_branch(name: str) -> None:
        if not _SAFE_BRANCH.fullmatch(name) or name.endswith((".", "/")) or ".." in name or "@{" in name:
            raise WorktreeError("invalid branch name")
