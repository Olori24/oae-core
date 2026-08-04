"""
Mission History Service.
"""

from oae.storage.service import StorageService


class HistoryService:
    """Stores mission execution history."""

    def __init__(self):
        self.storage = StorageService()
        self._key = "mission_history"

    def record(self, context):

        history = self.storage.load(self._key)

        if history is None:
            history = []

        history.append({
            "mission": context.mission,
            "success": context.success,
        })

        self.storage.save(self._key, history)

    def all(self):

        history = self.storage.load(self._key)

        return history if history else []

    def count(self):

        return len(self.all())

    def clear(self):

        self.storage.save(self._key, [])
