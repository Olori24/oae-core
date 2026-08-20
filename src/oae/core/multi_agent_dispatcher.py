from oae.core.dynamic_mission_prioritizer import (
    DynamicMissionPrioritizer,
)
from oae.core.engineering_director import EngineeringDirector


class MultiAgentDispatcher:
    """
    Dispatches prioritized missions to engineers.
    """

    def __init__(self):
        self.director = EngineeringDirector()
        self.prioritizer = DynamicMissionPrioritizer()

    def register(self, agent):
        self.director.register(agent)

    def add_mission(self, mission, priority=0):
        self.prioritizer.add(mission, priority)

    def dispatch(self):
        mission = self.prioritizer.next()

        if mission is None:
            return None

        return self.director.assign(mission)