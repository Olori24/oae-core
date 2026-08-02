import json
from pathlib import Path


class MemoryStore:

    def __init__(self, filename="memory.json"):
        self.path = Path(filename)

        if self.path.exists():
            self.memory = json.loads(self.path.read_text())
        else:
            self.memory = {}

    def save(self, key, value):
        self.memory[key] = value
        self.path.write_text(
            json.dumps(self.memory, indent=2)
        )

    def load(self, key):
        return self.memory.get(key)

    def all(self):
        return self.memory
