import json
from pathlib import Path

from oae.core.shared_agent_memory import SharedAgentMemory


class PersistentMemory(SharedAgentMemory):
    """
    Shared agent memory with persistence.
    """

    def __init__(self, path: str = "agent_memory.json"):
        super().__init__()
        self.path = Path(path)

        if self.path.exists():
            self.load()

    def save(self):
        data = {}

        for key, entry in self._memory.items():
            data[key] = {
                "author": entry.author,
                "key": entry.key,
                "value": entry.value,
            }

        self.path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

    def load(self):
        if not self.path.exists():
            return

        data = json.loads(
            self.path.read_text(encoding="utf-8")
        )

        for item in data.values():
            self.write(
                item["author"],
                item["key"],
                item["value"],
            )