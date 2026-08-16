from pathlib import Path


class WorkspaceManager:
    """
    Manages active engineering workspaces.
    """

    def __init__(self, root="workspace"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def repository_path(self, repository_name):
        return self.root / repository_name

    def create_workspace(self, repository_name):
        path = self.repository_path(repository_name)
        path.mkdir(parents=True, exist_ok=True)
        return path
