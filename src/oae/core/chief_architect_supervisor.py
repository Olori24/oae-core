from dataclasses import dataclass

from oae.core.agent_collaboration import AgentCollaboration


@dataclass
class MissionAssignment:
    mission: str
    completed: bool


class ChiefArchitectSupervisor:
    """
    Coordinates the complete AI Engineering Team.
    """

    def __init__(self):
        self.collaboration = AgentCollaboration()

    def execute(self, mission: str) -> MissionAssignment:

        self.collaboration.delegate(
            "Chief Architect",
            "Backend Engineer",
            mission,
        )

        self.collaboration.delegate(
            "Backend Engineer",
            "QA Engineer",
            mission,
        )

        self.collaboration.delegate(
            "QA Engineer",
            "Security Engineer",
            mission,
        )

        self.collaboration.delegate(
            "Security Engineer",
            "DevOps Engineer",
            mission,
        )

        return MissionAssignment(
            mission=mission,
            completed=True,
        )