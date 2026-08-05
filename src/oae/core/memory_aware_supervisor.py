from dataclasses import dataclass

from oae.core.agent_collaboration import AgentCollaboration
from oae.core.shared_agent_memory import SharedAgentMemory


@dataclass
class MissionResult:
    mission: str
    completed: bool


class MemoryAwareSupervisor:
    """
    Chief Architect with organizational memory.
    """

    def __init__(self):
        self.collaboration = AgentCollaboration()
        self.memory = SharedAgentMemory()

    def execute(self, mission: str):

        self.memory.write(
            "Chief Architect",
            f"mission:{mission}",
            "Mission Started",
        )

        self.collaboration.delegate(
            "Chief Architect",
            "Backend Engineer",
            mission,
        )

        return MissionResult(
            mission=mission,
            completed=True,
        )