from oae.core.autonomous_execution_pipeline import (
    AutonomousExecutionPipeline,
)

from oae.agents.cto_agent import CTOAgent
from oae.core.engineering_ledger import EngineeringLedger
from oae.core.engineering_memory import EngineeringMemory
from oae.core.engineering_recommendation_engine import (
    EngineeringRecommendationEngine,
)
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
        self.ledger = EngineeringLedger()
        self.memory = EngineeringMemory(self.ledger)
        self.recommendation_engine = EngineeringRecommendationEngine(
            self.memory
        )

    def register(self, agent):

        self.pipeline.register(agent)

    def review(self, missions):

        return self.cto.assign(missions)

    def execute_actions(self, actions):

        return self.executor.execute(actions)

    def assign(self, mission):

        return self.pipeline.execute(mission)

    def experience(self, query):
        return self.memory.experience_report(query)

    def recommend(self, query):
        return self.recommendation_engine.recommend(query)
