from oae.core.autonomous_engineering_planner import (
    AutonomousEngineeringPlanner,
)
from oae.core.autonomous_verification_pipeline import (
    AutonomousVerificationPipeline,
)
from oae.core.patch_generator import PatchGenerator


class RepositoryRecoveryEngine:
    """
    Coordinates autonomous repository recovery.
    """

    def __init__(self):
        self.planner = AutonomousEngineeringPlanner()
        self.generator = PatchGenerator()
        self.verifier = AutonomousVerificationPipeline()

    def recover(self, recommendations):
        plans = self.planner.create_plan(recommendations)

        patches = [
            self.generator.generate(plan)
            for plan in plans
        ]

        verification = [
            self.verifier.verify(patch)
            for patch in patches
        ]

        return {
            "plans": plans,
            "patches": patches,
            "verification": verification,
        }
