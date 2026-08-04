"""
Generic persistent storage service.
"""


class StorageService:
    """Simple key/value storage."""

    def __init__(self):
        self._data = {}

    def save(self, key, value):
        self._data[key] = value

    def load(self, key):
        return self._data.get(key)

    def exists(self, key):
        return key in self._data

    def delete(self, key):
        return self._data.pop(key, None) is not None

    def keys(self):
        return list(self._data.keys())

    def clear(self):
        self._data.clear()
