from oae.core.autonomous_fix_planner import (
    AutonomousFixPlanner,
)
from oae.core.failure_classifier import (
    FailureClassifier,
)
from oae.core.risk_engine import (
    RiskEngine,
)


class FailureRecoveryCoordinator:
    """
    Converts execution failures into controlled
    engineering recovery plans.
    """

    def __init__(self):

        self.classifier = FailureClassifier()
        self.risk_engine = RiskEngine()
        self.fix_planner = AutonomousFixPlanner()

    def recover(self, execution_result, mission):

        failure_type = self.classifier.classify(
            execution_result
        )

        if failure_type == "NO_FAILURE":

            return {
                "status": "no_recovery_required",
                "failure_type": failure_type,
                "mission": mission,
            }

        risk = self.risk_engine.assess(
            "modify"
        )

        plan = self.fix_planner.plan(
            mission
        )

        return {
            "status": "recovery_required",
            "failure_type": failure_type,
            "risk": {
                "action": risk.action,
                "level": risk.level,
                "score": risk.score,
            },
            "plan": plan,
            "mission": mission,
        }
