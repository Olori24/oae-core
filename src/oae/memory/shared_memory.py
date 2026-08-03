from .store import MemoryStore


class SharedMemory:
    """High-level shared memory interface for OAE agents."""

    def __init__(self):
        self.store = MemoryStore()

    def write(self, key, value):
        existing = self.store.load(key)

        if isinstance(existing, dict):
            version = existing.get("version", 0) + 1
        else:
            version = 1

        self.store.save(
            key,
            {
                "value": value,
                "version": version,
            },
        )

    def read(self, key):
        entry = self.store.load(key)

        if isinstance(entry, dict):
            return entry.get("value")

        return entry

    def exists(self, key):
        return self.store.load(key) is not None

    def delete(self, key):
        return self.store.delete(key)

    def clear(self):
        self.store.clear()

    def keys(self):
        return list(self.store.all().keys())
