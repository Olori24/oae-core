from oae.core.decision_engine import DecisionEngine
from oae.core.engineering_ledger import EngineeringLedger
from oae.security import ApprovalGate, SecurityPolicy


class SecureExecutionPipeline:
    """
    Coordinates secure engineering decisions.
    """

    def __init__(self):
        self.decision_engine = DecisionEngine()
        self.ledger = EngineeringLedger()
        self.approval_gate = ApprovalGate(SecurityPolicy())

    def evaluate(self, action: str, target: str, confidence: float):
        decision = self.decision_engine.evaluate(action, confidence)

        self.ledger.record(
            "DECISION_CREATED",
            f"{action}:{confidence}",
        )

        if decision.requires_approval:
            request = self.approval_gate.approve(
                action=action,
                target=target,
                requester="DecisionEngine",
            )

            self.ledger.record(
                "APPROVAL_REQUIRED",
                action,
            )

            return request

        self.ledger.record(
            "AUTO_APPROVED",
            action,
        )

        return decision