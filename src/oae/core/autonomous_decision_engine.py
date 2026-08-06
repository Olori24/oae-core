from oae.core.engineering_consciousness import (
    EngineeringConsciousness,
)
from oae.core.repository_health_score import (
    RepositoryHealthScore,
)


class AutonomousDecisionEngine:
    """
    Makes explainable engineering decisions.
    """

    def __init__(self):
        self.consciousness = EngineeringConsciousness()
        self.health = RepositoryHealthScore()

    def decide(
        self,
        mission,
        health_score=100,
    ):
        consciousness = self.consciousness.evaluate(mission)

        approved = (
            consciousness["confidence"] >= 0.90
            and health_score >= 50
        )

        return {
            "approved": approved,
            "objective": consciousness["objective"],
            "reason": consciousness["reason"],
            "risk": consciousness["risk"],
            "confidence": consciousness["confidence"],
            "repository_health": health_score,
            "rollback_required": consciousness["rollback_required"],
            "verification_plan": consciousness["verification_plan"],
        }