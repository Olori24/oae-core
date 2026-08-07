from pathlib import Path

from oae.core.repository_worktree_manager import (
    RepositoryWorktreeManager,
)

from oae.core.git_branch_manager import (
    GitBranchManager,
)

from oae.core.real_patch_engine import (
    RealPatchEngine,
)


class RepositoryExecutionEngine:
    """
    Executes engineering operations inside isolated worktrees.
    """

    def __init__(self):

        self.worktree = RepositoryWorktreeManager()
        self.branch_manager = GitBranchManager()
        self.patch_engine = RealPatchEngine()

    def execute(
        self,
        original: str,
        modified: str,
        filename: str = "file.py",
    ):
        """
        Backward-compatible patch execution API.
        """

        workspace = self.worktree.create_worktree()

        branch = self.branch_manager.create_branch(
            "oae-engineering"
        )

        patch = self.patch_engine.generate_patch(
            original,
            modified,
            filename,
        )

        return {
            "workspace": workspace,
            "branch": branch,
            "patch": patch,
            "status": "completed",
        }

    def execute_operation(self, operation: dict):
        """
        Execute a repository operation.

        Supported operations:
        - create_file
        - modify_file
        - run_tests
        - commit_changes
        """

        operation_type = operation.get("operation")

        if operation_type in {
            "create_file",
            "modify_file",
        }:

            path = operation.get("path")

            content = operation.get(
                "content",
                "",
            )

            if not path:
                return {
                    "status": "error",
                    "operation": operation_type,
                    "error": "Missing file path",
                }

            workspace = self.worktree.create_worktree()

            file_path = (
                Path(workspace["path"]) / path
            )

            file_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            file_path.write_text(
                content,
                encoding="utf-8",
            )

            return {
                "status": "completed",
                "operation": operation_type,
                "path": path,
                "workspace": workspace,
            }

        return {
            "status": "accepted",
            "operation": operation_type,
        }
