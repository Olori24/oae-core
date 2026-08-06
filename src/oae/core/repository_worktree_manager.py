import tempfile
import shutil
from pathlib import Path


class RepositoryWorktreeManager:
    """
    Manages temporary worktrees for safe engineering execution.
    """

    def create_worktree(self):
        path = tempfile.mkdtemp(prefix="oae_worktree_")
        return {
            "created": True,
            "path": path,
        }

    def remove_worktree(self, path):
        path = Path(path)

        if path.exists():
            shutil.rmtree(path)

        return {
            "removed": True,
            "path": str(path),
        }
