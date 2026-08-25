from pathlib import Path

from oae.core.process_security import run_git


class RepositoryUpdateEngine:
    """
    Updates an existing Git repository.
    """

    def update(self, repository_path):
        repository_path = Path(repository_path).resolve()

        if not repository_path.is_dir():
            raise FileNotFoundError(repository_path)
        if not (repository_path / ".git").is_dir():
            raise ValueError("Repository update requires a Git worktree.")

        run_git(
            ["pull", "--ff-only"],
            cwd=repository_path,
            check=True,
        )

        return repository_path
