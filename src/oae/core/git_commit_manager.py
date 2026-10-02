from pathlib import Path
from typing import Any

from oae.core.process_security import ProcessPolicyError, run_git


class GitCommitManager:
    """Creates bounded commits inside an already-isolated Git workspace."""

    def commit(
        self,
        cwd: str | Path,
        message: str,
        paths: list[str] | None = None,
    ) -> dict[str, Any]:
        root = Path(cwd).resolve()
        if not root.is_dir():
            raise ProcessPolicyError("Git workspace does not exist.")
        if not isinstance(message, str) or not message.strip() or "\x00" in message:
            raise ProcessPolicyError("Commit message must be non-empty text.")

        selected = paths or ["."]
        safe_paths: list[str] = []
        for path in selected:
            if not isinstance(path, str) or not path or "\x00" in path:
                raise ProcessPolicyError("Commit path is invalid.")
            candidate = (root / path).resolve()
            if candidate != root and root not in candidate.parents:
                raise ProcessPolicyError("Commit path escapes the Git workspace.")
            safe_paths.append(path)

        add = run_git(["add", "--", *safe_paths], cwd=root, check=False)
        if add.returncode != 0:
            raise ProcessPolicyError(add.stderr.strip() or "Git staging failed.")

        commit = run_git(["commit", "-m", message], cwd=root, check=False)
        if commit.returncode != 0:
            return {
                "status": "failed",
                "returncode": commit.returncode,
                "stdout": commit.stdout,
                "stderr": commit.stderr,
            }

        revision = run_git(["log", "-1", "--format=%H"], cwd=root, check=True)
        return {
            "status": "committed",
            "commit_sha": revision.stdout.strip(),
            "workspace": str(root),
            "stdout": commit.stdout,
            "stderr": commit.stderr,
        }
