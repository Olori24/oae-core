import heapq
from dataclasses import dataclass, field


@dataclass(order=True)
class PriorityMission:
    priority: int
    objective: str = field(compare=False)


class PriorityMissionQueue:
    """
    Priority queue for engineering missions.
    Lower priority numbers execute first.
    """

    def __init__(self):
        self._queue = []

    def enqueue(self, objective: str, priority: int):
        mission = PriorityMission(priority, objective)
        heapq.heappush(self._queue, mission)
        return mission

    def dequeue(self):
        if not self._queue:
            return None

        return heapq.heappop(self._queue)

    def peek(self):
        if not self._queue:
            return None

        return self._queue[0]

    def size(self):
        return len(self._queue)

    def empty(self):
        return len(self._queue) == 0