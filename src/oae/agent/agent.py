from .mission import Mission
from .state import AgentState

from oae.planner.planner import Planner
from oae.providers.manager import ProviderManager


class Agent:

    def __init__(self):
        self.state = AgentState()
        self.planner = Planner()
        self.providers = ProviderManager()

    def run(self, goal: str):

        mission = Mission(goal)

        self.state.status = "planning"

        tasks = self.planner.create_plan(goal)

        print("\nMission Plan:\n")

        for task in tasks:
            print(f" • {task.description}")

        self.state.status = "routing"

        provider = self.providers.get()

        result = provider.generate(goal)

        self.state.status = "completed"

        mission.finish()

        return result
