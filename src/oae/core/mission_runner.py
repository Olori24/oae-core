"""
Mission orchestration for OAE.
"""

from oae.core.decision_engine import DecisionEngine
from oae.core.engineering_ledger import EngineeringLedger
from oae.core.secure_pipeline import SecureExecutionPipeline


class MissionRunner:
    """
    Coordinates execution of engineering missions.
    """

    def __init__(self):
        self.pipeline = SecureExecutionPipeline()
        self.ledger = EngineeringLedger()
        self.decision_engine = DecisionEngine()

    def run(self, action: str, target: str, confidence: float):
        self.ledger.record(
            "MISSION_STARTED",
            f"{action}:{target}",
        )

        result = self.pipeline.evaluate(
            action=action,
            target=target,
            confidence=confidence,
        )

        self.ledger.record(
            "MISSION_FINISHED",
            action,
        )

        return result