"""
Repository sandbox for safe engineering operations.
"""

from pathlib import Path
import shutil
import tempfile


class RepositorySandbox:
    def __init__(self):
        self._path = Path(tempfile.mkdtemp(prefix="oae_"))

    def clone(self):
        """
        Placeholder for future git clone.
        Currently just returns the sandbox path.
        """
        return self._path

    def workspace_path(self):
        return self._path

    def cleanup(self):
        if self._path.exists():
            shutil.rmtree(self._path)