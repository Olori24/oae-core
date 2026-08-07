from pathlib import Path


class RepositoryWorkspaceController:
    """
    Tracks repositories managed by OAE.
    """

    def __init__(self, workspace="workspace"):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def repository_path(self, repository_name):
        return self.workspace / repository_name

    def exists(self, repository_name):
        return self.repository_path(repository_name).exists()

    def create(self, repository_name):
        path = self.repository_path(repository_name)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_repositories(self):
        return sorted(
            [
                p.name
                for p in self.workspace.iterdir()
                if p.is_dir()
            ]
        )
