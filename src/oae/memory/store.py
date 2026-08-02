class MemoryStore:

    def __init__(self):
        self._store = {}

    def save(self, key, value):
        self._store[key] = value

    def load(self, key):
        return self._store.get(key)

    def delete(self, key):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()

    def keys(self):
        return list(self._store.keys())
