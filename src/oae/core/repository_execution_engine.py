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
        Backward-compatible execution API.
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
        New engineering-operation API.
        """

        return {
            "status": "accepted",
            "operation": operation.get("operation"),
        }
