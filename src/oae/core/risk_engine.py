from dataclasses import dataclass


@dataclass
class RiskAssessment:
    action: str
    level: str
    score: int


class RiskEngine:
    """
    Evaluates engineering risk for proposed actions.
    """

    RISK_TABLE = {
        "read": ("LOW", 10),
        "test": ("LOW", 20),
        "refactor": ("MEDIUM", 50),
        "modify": ("MEDIUM", 60),
        "delete": ("HIGH", 90),
        "force_push": ("CRITICAL", 100),
    }

    def assess(self, action: str) -> RiskAssessment:
        level, score = self.RISK_TABLE.get(
            action,
            ("UNKNOWN", 75),
        )

        return RiskAssessment(
            action=action,
            level=level,
            score=score,
        )