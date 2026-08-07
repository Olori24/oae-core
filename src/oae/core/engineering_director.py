from oae.core.autonomous_execution_pipeline import (
    AutonomousExecutionPipeline,
)

from oae.agents.cto_agent import CTOAgent
from oae.agents.engineering_action_executor import (
    EngineeringActionExecutor,
)


class EngineeringDirector:
    """
    Oversees engineering mission execution.
    """

    def __init__(self):

        self.pipeline = AutonomousExecutionPipeline()
        self.cto = CTOAgent()
        self.executor = EngineeringActionExecutor()

    def register(self, agent):

        self.pipeline.register(agent)

    def review(self, missions):

        return self.cto.assign(missions)

    def execute_actions(self, actions):

        return self.executor.execute(actions)

    def assign(self, mission):

        return self.pipeline.execute(mission)
