"""
Repository Inspector.
"""

from pathlib import Path

from .profile import RepositoryProfile
from .detector_registry import DetectorRegistry


class RepositoryInspector:

    def __init__(self):

        self.detectors = DetectorRegistry().load()

    def inspect(self, root="."):

        root = Path(root)

        profile = RepositoryProfile()

        profile.has_git = (root / ".git").exists()
        profile.has_readme = (root / "README.md").exists()
        profile.has_pyproject = (root / "pyproject.toml").exists()
        profile.uses_pytest = (root / "tests").exists()

        for detector in self.detectors:
            detector.detect(root, profile)

        return profile
