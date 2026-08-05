from oae.core.autonomous_execution_pipeline import (
    AutonomousExecutionPipeline,
)


class EngineeringDirector:
    """
    Oversees engineering mission execution.
    """

    def __init__(self):
        self.pipeline = AutonomousExecutionPipeline()

    def register(self, agent):
        self.pipeline.register(agent)

    def assign(self, mission):
        return self.pipeline.execute(mission)