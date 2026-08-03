import json
from pathlib import Path


class SharedMemory:
    """Persistent shared memory for OAE agents."""

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
        existing = self._memory.get(key)

        if isinstance(existing, dict):
            version = existing.get("version", 0) + 1
        else:
            version = 1

        self._memory[key] = {
            "value": value,
            "version": version,
        }

        self._save()

    def read(self, key):
        entry = self._memory.get(key)

        if isinstance(entry, dict):
            return entry.get("value")

        return entry

    def exists(self, key):
        return key in self._memory

    def keys(self):
        return list(self._memory.keys())
