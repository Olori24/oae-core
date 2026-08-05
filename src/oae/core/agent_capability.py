from dataclasses import dataclass, field


@dataclass
class AgentCapability:
    name: str
    capabilities: list[str] = field(default_factory=list)


class AgentCapabilityEngine:
    """
    Stores and queries engineering capabilities.
    """

    def __init__(self):
        self._agents = {}

    def register(self, name: str, capabilities: list[str]):
        self._agents[name] = AgentCapability(
            name=name,
            capabilities=capabilities,
        )

    def find(self, capability: str):
        return [
            agent
            for agent in self._agents.values()
            if capability in agent.capabilities
        ]

    def exists(self, name: str):
        return name in self._agents

    def count(self):
        return len(self._agents)