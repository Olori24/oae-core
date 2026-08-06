import shutil
from pathlib import Path


class RepositoryCloneEngine:
    """
    Creates a local working copy of a repository.
    """

    def clone(self, source, destination):
        source = Path(source)
        destination = Path(destination)

        shutil.copytree(source, destination)

        return {
            "status": "cloned",
            "source": str(source),
            "destination": str(destination),
        }
