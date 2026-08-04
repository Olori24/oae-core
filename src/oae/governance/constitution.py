"""
Constitution loader.
"""

from pathlib import Path


class Constitution:

    def __init__(self, path="docs/constitution.md"):
        self.path = Path(path)
        self.content = ""

    def load(self):
        """Load the Constitution from disk."""

        self.content = self.path.read_text(encoding="utf-8")

        return self.content

    def loaded(self):
        return bool(self.content.strip())
