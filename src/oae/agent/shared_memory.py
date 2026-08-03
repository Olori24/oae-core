class SharedMemory:

    def __init__(self):
        self.data = {}

    def write(self, key, value):
        self.data[key] = value

    def read(self, key):
        return self.data.get(key)

    def keys(self):
        return list(self.data.keys())
