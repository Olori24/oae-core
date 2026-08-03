from oae.memory.shared_memory import SharedMemory


class Orchestrator:
    """Coordinates OAE agents."""

    def __init__(self):
        self.memory = SharedMemory()

    def remember(self, key, value):
        self.memory.write(key, value)

    def recall(self, key):
        return self.memory.read(key)

    def list_memory(self):
        return self.memory.keys()
