class MissionQueue:

    def __init__(self):
        self.queue = []

    def add(self, mission):
        self.queue.append(mission)

    def next(self):
        if not self.queue:
            return None
        return self.queue.pop(0)

    def size(self):
        return len(self.queue)
