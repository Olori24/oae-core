from dataclasses import dataclass


@dataclass
class MemoryEntry:
    author: str
    key: str
    value: str


class SharedAgentMemory:
    """
    Shared engineering memory used by all AI agents.
    """

    def __init__(self):
        self._memory: dict[str, MemoryEntry] = {}

    def write(self, author: str, key: str, value: str):
        self._memory[key] = MemoryEntry(
            author=author,
            key=key,
            value=value,
        )

    def read(self, key: str):
        return self._memory.get(key)

    def exists(self, key: str):
        return key in self._memory

    def keys(self):
        return list(self._memory.keys())