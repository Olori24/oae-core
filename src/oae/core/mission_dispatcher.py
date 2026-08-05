from dataclasses import dataclass

from oae.core.priority_mission_queue import PriorityMissionQueue
from oae.core.task_scheduler import TaskScheduler


@dataclass
class DispatchResult:
    objective: str
    dispatched: bool


class MissionDispatcher:
    """
    Dispatches missions from the priority queue to the scheduler.
    """

    def __init__(self):
        self.queue = PriorityMissionQueue()
        self.scheduler = TaskScheduler()

    def dispatch(self):
        mission = self.queue.dequeue()

        if mission is None:
            return None

        self.scheduler.schedule(
            "Chief Architect",
            mission.objective,
        )

        return DispatchResult(
            objective=mission.objective,
            dispatched=True,
        )