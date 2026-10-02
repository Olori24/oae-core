from pathlib import Path
from typing import Any

from oae.core.git_branch_manager import GitBranchManager
from oae.core.real_patch_engine import RealPatchEngine
from oae.core.repository_test_runner import RepositoryTestRunner
from oae.core.repository_worktree_manager import RepositoryWorktreeManager
from oae.security.kernel import SecurityKernel


class RepositoryExecutionEngine:
    """Executes bounded engineering operations inside an isolated workspace."""

    def __init__(self, security: SecurityKernel | None = None):
        self.security = security or SecurityKernel()
        self.worktree = RepositoryWorktreeManager()
        self.branch_manager = GitBranchManager()
        self.patch_engine = RealPatchEngine()
        self.test_runner = RepositoryTestRunner()

    def execute(self, original: str, modified: str, filename: str = "file.py") -> dict[str, Any]:
        workspace = self.worktree.create_worktree()
        branch = self.branch_manager.create_branch("oae-engineering")
        patch = self.patch_engine.generate_patch(original, modified, filename)
        return {"workspace": workspace, "branch": branch, "patch": patch, "status": "completed"}

    def execute_operations(
        self, operations: list[dict[str, Any]], workspace_path: str | Path
    ) -> list[dict[str, Any]]:
        """Execute bounded operations against one caller-provided isolated workspace."""
        root = Path(workspace_path).resolve()
        if not root.is_dir():
            raise ValueError("Execution workspace does not exist.")

        results: list[dict[str, Any]] = []
        for operation in operations:
            item = dict(operation)
            item["workspace_path"] = str(root)
            results.append(self.execute_operation(item))
        return results

    def execute_operation(self, operation: dict[str, Any]) -> dict[str, Any]:
        operation_type = operation.get("operation")

        if operation_type in {"create_file", "modify_file"}:
            if not self.security.authorize("write_repository"):
                return {
                    "status": "denied",
                    "operation": operation_type,
                    "error": "Security authorization denied",
                }

            path = operation.get("path")
            content = operation.get("content", "")
            if not isinstance(path, str) or not path:
                return {
                    "status": "error",
                    "operation": operation_type,
                    "error": "Missing file path",
                }

            workspace_path = operation.get("workspace_path")
            if workspace_path is not None and not isinstance(workspace_path, (str, Path)):
                return {
                    "status": "error",
                    "operation": operation_type,
                    "error": "Invalid workspace path",
                }

            workspace = (
                {"created": False, "path": str(Path(workspace_path).resolve())}
                if workspace_path is not None
                else self.worktree.create_worktree()
            )
            root = Path(workspace["path"]).resolve()
            file_path = (root / path).resolve()
            if file_path != root and root not in file_path.parents:
                return {
                    "status": "denied",
                    "operation": operation_type,
                    "error": "File path escapes the execution workspace",
                }
            if operation_type == "modify_file" and not file_path.exists():
                return {
                    "status": "error",
                    "operation": operation_type,
                    "path": path,
                    "error": "Target file does not exist",
                }

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return {
                "status": "completed",
                "operation": operation_type,
                "path": path,
                "workspace": workspace,
            }

        if operation_type == "run_tests":
            command = operation.get("command", ["python", "--version"])
            cwd = operation.get("cwd") or operation.get("workspace_path")
            if cwd is not None and not isinstance(cwd, (str, Path)):
                return {
                    "status": "error",
                    "operation": "run_tests",
                    "error": "Invalid test working directory",
                }
            result = self.test_runner.run(command=command, cwd=cwd)
            return {"status": "completed", "operation": "run_tests", "result": result}

        return {"status": "accepted", "operation": operation_type}
