"""
Kernel Event Bus.
"""


class EventBus:
    """Simple publish/subscribe event bus."""

    def __init__(self):
        self._listeners = {}

    def subscribe(self, event, callback):
        self._listeners.setdefault(event, []).append(callback)

    def publish(self, event, data=None):
        for callback in self._listeners.get(event, []):
            callback(data)

    def listeners(self, event):
        return list(self._listeners.get(event, []))
