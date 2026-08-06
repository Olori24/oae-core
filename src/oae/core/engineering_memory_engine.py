class EngineeringMemoryEngine:
    """
    Stores and retrieves engineering knowledge gathered over time.
    """

    def __init__(self):
        self._memory = {}

    def remember(self, key, value):
        self._memory[key] = value

    def recall(self, key):
        return self._memory.get(key)

    def forget(self, key):
        self._memory.pop(key, None)

    def all(self):
        return dict(self._memory)
