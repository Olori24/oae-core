from oae.core.autonomous_engineering_pipeline import (
    AutonomousEngineeringPipeline,
)
from oae.core.engineering_state_manager import (
    EngineeringStateManager,
)
from oae.core.execution_feedback import ExecutionFeedback


class AutonomousEngineeringCycle:
    """
    Runs one complete autonomous engineering cycle.
    """

    def __init__(self):
        self.pipeline = AutonomousEngineeringPipeline()
        self.feedback = ExecutionFeedback()
        self.state = EngineeringStateManager()

    def register(self, agent):
        self.pipeline.register(agent)

    def execute(self, repository_profile):
        results = self.pipeline.execute(repository_profile)

        self.state.set(
            "completed_missions",
            len(results),
        )

        return results