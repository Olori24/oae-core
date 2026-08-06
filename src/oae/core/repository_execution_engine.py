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
        self.git = GitBranchManager()
        self.patch = RealPatchEngine()

    def execute(
        self,
        original,
        modified,
        filename="file.py",
    ):
        workspace = self.worktree.create_worktree()

        branch = self.git.create_branch(
            "oae/execution"
        )

        patch = self.patch.generate_patch(
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
