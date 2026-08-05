from dataclasses import dataclass

from oae.core.risk_engine import RiskEngine


@dataclass
class Decision:
    action: str
    confidence: float
    risk: str
    requires_approval: bool


class DecisionEngine:
    """
    Makes engineering decisions using confidence and risk.
    """

    def __init__(self):
        self.risk_engine = RiskEngine()

    def evaluate(self, action: str, confidence: float) -> Decision:
        assessment = self.risk_engine.assess(action)

        requires_approval = (
            confidence < 0.90
            or assessment.level in ("HIGH", "CRITICAL")
        )

        return Decision(
            action=action,
            confidence=confidence,
            risk=assessment.level,
            requires_approval=requires_approval,
        )