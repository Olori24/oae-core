from pathlib import Path

from oae.core.repository_worktree_manager import RepositoryWorktreeManager
from oae.core.git_branch_manager import GitBranchManager
from oae.core.real_patch_engine import RealPatchEngine
from oae.core.repository_test_runner import RepositoryTestRunner
from oae.security.kernel import SecurityKernel


class RepositoryExecutionEngine:
    """Executes engineering operations inside isolated worktrees."""

    def __init__(self, security=None):
        self.security = security or SecurityKernel()
        self.worktree = RepositoryWorktreeManager()
        self.branch_manager = GitBranchManager()
        self.patch_engine = RealPatchEngine()
        self.test_runner = RepositoryTestRunner()

    def execute(self, original: str, modified: str, filename: str = "file.py"):
        workspace = self.worktree.create_worktree()
        branch = self.branch_manager.create_branch("oae-engineering")
        patch = self.patch_engine.generate_patch(original, modified, filename)
        return {"workspace": workspace, "branch": branch, "patch": patch, "status": "completed"}

    def execute_operation(self, operation: dict):
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
            if not path:
                return {"status": "error", "operation": operation_type, "error": "Missing file path"}

            workspace = self.worktree.create_worktree()
            file_path = Path(workspace["path"]) / path
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
            cwd = operation.get("cwd")
            result = self.test_runner.run(command=command, cwd=cwd)
            return {"status": "completed", "operation": "run_tests", "result": result}

        return {"status": "accepted", "operation": operation_type}
