from dataclasses import dataclass


@dataclass
class Decision:
    action: str
    confidence: float
    requires_approval: bool


class DecisionEngine:
    """
    Evaluates engineering decisions before execution.
    """

    def evaluate(self, action: str, confidence: float) -> Decision:
        return Decision(
            action=action,
            confidence=confidence,
            requires_approval=confidence < 0.90,
        )