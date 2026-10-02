from pathlib import Path
from typing import Any

from oae.core.process_security import ProcessPolicyError, run_git, validate_git_ref


class GitBranchManager:
    """Creates and manages Git branches inside an explicitly supplied workspace.

    Without a workspace this retains the legacy descriptive behavior for compatibility.
    Real Git mutation is only performed when a concrete workspace is supplied.
    """

    def create_branch(self, name: str, cwd: str | Path | None = None) -> dict[str, Any]:
        name = validate_git_ref(name)
        if cwd is None:
            return {"status": "created", "branch": name}
        result = run_git(["checkout", "-b", name], cwd=cwd, check=False)
        if result.returncode != 0:
            raise ProcessPolicyError(result.stderr.strip() or "Git branch creation failed.")
        return {"status": "created", "branch": name, "workspace": str(Path(cwd).resolve())}

    def checkout(self, name: str, cwd: str | Path | None = None) -> dict[str, Any]:
        name = validate_git_ref(name)
        if cwd is None:
            return {"status": "checked_out", "branch": name}
        result = run_git(["checkout", name], cwd=cwd, check=False)
        if result.returncode != 0:
            raise ProcessPolicyError(result.stderr.strip() or "Git checkout failed.")
        return {"status": "checked_out", "branch": name, "workspace": str(Path(cwd).resolve())}

    def current_branch(self, cwd: str | Path | None = None) -> str:
        if cwd is None:
            return "main"
        result = run_git(["branch", "--show-current"], cwd=cwd, check=True)
        return result.stdout.strip()

    def delete_branch(self, name: str, cwd: str | Path | None = None) -> dict[str, Any]:
        name = validate_git_ref(name)
        if cwd is None:
            return {"status": "deleted", "branch": name}
        result = run_git(["branch", "-D", name], cwd=cwd, check=False)
        if result.returncode != 0:
            raise ProcessPolicyError(result.stderr.strip() or "Git branch deletion failed.")
        return {"status": "deleted", "branch": name, "workspace": str(Path(cwd).resolve())}
