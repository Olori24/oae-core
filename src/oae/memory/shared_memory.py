import json
from pathlib import Path


class SharedMemory:
    """Simple shared memory for OAE agents with persistence."""

    def __init__(self, file_path="memory.json"):
        self.file_path = Path(file_path)
        self._memory = {}
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r") as f:
                    self._memory = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._memory = {}

    def _save(self):
        with open(self.file_path, "w") as f:
            json.dump(self._memory, f, indent=2)

    def write(self, key, value):
        self._memory[key] = value
        self._save()

    def read(self, key):
        return self._memory.get(key)

    def keys(self):
        return list(self._memory.keys())
