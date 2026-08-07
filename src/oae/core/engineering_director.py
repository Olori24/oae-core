from oae.core.autonomous_execution_pipeline import (
    AutonomousExecutionPipeline,
)

from oae.agents.cto_agent import CTOAgent


class EngineeringDirector:
    """
    Oversees engineering mission execution.
    """

    def __init__(self):

        self.pipeline = AutonomousExecutionPipeline()

        self.cto = CTOAgent()

    def register(self, agent):

        self.pipeline.register(agent)

    def review(self, missions):
        """
        Ask the CTO Agent to assign engineering work.
        """

        return self.cto.assign(missions)

    def assign(self, mission):

        return self.pipeline.execute(mission)
