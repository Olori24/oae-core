"""
Architecture Decision Record (ADR) repository.
"""

from pathlib import Path


class ADRRepository:

    def __init__(self, directory="docs/adr"):
        self.directory = Path(directory)
        self.documents = {}

    def load(self):
        """Load all ADR documents."""

        self.documents.clear()

        for file in sorted(self.directory.glob("*.md")):
            self.documents[file.name] = file.read_text(encoding="utf-8")

        return self.documents

    def loaded(self):
        return len(self.documents) > 0
