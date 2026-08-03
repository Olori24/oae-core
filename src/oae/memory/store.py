import json
from pathlib import Path


class MemoryStore:
    """Handles persistent storage for OAE memory."""

    def __init__(self, filename="memory.json"):
        self.path = Path(filename)
        self.memory = {}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                self.memory = json.loads(self.path.read_text())
            except json.JSONDecodeError:
                self.memory = {}

    def _save(self):
        self.path.write_text(
            json.dumps(self.memory, indent=2)
        )

    def save(self, key, value):
        self.memory[key] = value
        self._save()

    def load(self, key):
        return self.memory.get(key)

    def delete(self, key):
        if key in self.memory:
            del self.memory[key]
            self._save()
            return True
        return False

    def clear(self):
        self.memory.clear()
        self._save()

    def all(self):
        return self.memory
