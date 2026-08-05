from dataclasses import dataclass


@dataclass
class RegisteredAgent:
    name: str
    role: str


class AgentRegistry:
    """
    Stores and manages registered AI engineers.
    """

    def __init__(self):
        self._agents = {}

    def register(self, name: str, role: str):
        agent = RegisteredAgent(name, role)
        self._agents[name] = agent
        return agent

    def get(self, name: str):
        return self._agents.get(name)

    def all(self):
        return list(self._agents.values())

    def exists(self, name: str):
        return name in self._agents

    def count(self):
        return len(self._agents)