from pathlib import Path

from oae.core.process_security import repository_name_from_url, run_git, validate_repository_url


class RepositoryCloneEngine:
    """
    Clone or update a Git repository.
    """

    def __init__(self, workspace="workspace"):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def clone(self, url):
        clone_url = validate_repository_url(url)
        name = repository_name_from_url(clone_url)
        workspace = self.workspace.resolve()
        destination = (workspace / name).resolve()
        if destination.parent != workspace:
            raise ValueError("Repository destination escaped the configured workspace.")

        if destination.exists():
            if not (destination / ".git").is_dir():
                raise ValueError("Existing repository destination is not a Git worktree.")
            run_git(
                ["pull", "--ff-only"],
                cwd=destination,
                check=True,
            )
        else:
            run_git(
                ["clone", clone_url, str(destination)],
                cwd=workspace,
                check=True,
            )

        return destination
