from collections import deque
from dataclasses import dataclass


@dataclass
class QueuedMission:
    objective: str


class MissionQueue:
    """
    FIFO queue for engineering missions.
    """

    def __init__(self):
        self._queue: deque[QueuedMission] = deque()

    def enqueue(self, objective: str):
        mission = QueuedMission(objective)
        self._queue.append(mission)
        return mission

    def dequeue(self):
        if not self._queue:
            return None

        return self._queue.popleft()

    def peek(self):
        if not self._queue:
            return None

        return self._queue[0]

    def size(self):
        return len(self._queue)

    def empty(self):
        return len(self._queue) == 0
