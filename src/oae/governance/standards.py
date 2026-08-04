"""
Governance Standards loader.
"""

from pathlib import Path


class Standards:

    def __init__(self, directory="docs/governance"):
        self.directory = Path(directory)
        self.documents = {}

    def load(self):
        """Load all governance standards."""

        self.documents.clear()

        for file in sorted(self.directory.glob("*.md")):
            self.documents[file.name] = file.read_text(encoding="utf-8")

        return self.documents

    def loaded(self):
        return len(self.documents) > 0
