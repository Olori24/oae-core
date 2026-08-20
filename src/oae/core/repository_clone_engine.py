import subprocess
from pathlib import Path


class RepositoryCloneEngine:
    """
    Clone or update a Git repository.
    """

    def __init__(self, workspace="workspace"):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def clone(self, url):
        name = url.rstrip("/").split("/")[-1]

        if name.endswith(".git"):
            name = name[:-4]

        destination = self.workspace / name

        if destination.exists():
            subprocess.run(
                ["git", "-C", str(destination), "pull"],
                check=True,
            )
        else:
            subprocess.run(
                ["git", "clone", url, str(destination)],
                check=True,
            )

        return destination
