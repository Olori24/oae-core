from .mission import Mission
from .state import AgentState

from oae.providers.manager import ProviderManager


class Agent:

    def __init__(self):
        self.state = AgentState()
        self.providers = ProviderManager()

    def run(self, goal: str):

        mission = Mission(goal)

        self.state.status = "running"

        provider = self.providers.get()

        result = provider.generate(goal)

        mission.finish()

        self.state.status = "completed"

        return result
