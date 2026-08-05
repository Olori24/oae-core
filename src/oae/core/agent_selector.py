from oae.core.agent_capability import AgentCapabilityEngine
from oae.core.workload_manager import WorkloadManager


class AgentSelector:
    """
    Selects the least busy qualified engineer.
    """

    def __init__(self):
        self.engine = AgentCapabilityEngine()
        self.workload = WorkloadManager()

    def register_agent(self, name: str, capabilities: list[str]):
        self.engine.register(name, capabilities)
        self.workload.register(name)

    def select(self, capability: str):
        matches = self.engine.find(capability)

        if not matches:
            return None

        return min(
            matches,
            key=lambda agent: self.workload.workload(agent.name),
        )