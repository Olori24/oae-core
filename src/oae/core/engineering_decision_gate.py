from dataclasses import dataclass


@dataclass
class EngineeringDecision:
    """
    Advisory decision produced from an engineering recommendation.

    This object does not execute missions.
    """

    mission: str
    recommendation: dict
    decision: str
    reason: str

    def to_dict(self):
        return {
            "mission": self.mission,
            "recommendation": self.recommendation,
            "decision": self.decision,
            "reason": self.reason,
        }


class EngineeringDecisionGate:
    """
    Converts engineering recommendations into explicit decision states.

    Decision states:
        proceed - safe to continue through the normal approval path.
        review   - requires engineering/CTO review.
        hold     - should not proceed without explicit intervention.
    """

    def evaluate(self, mission, recommendation):
        action = recommendation.get("recommendation")

        if action == "increase_verification":
            return EngineeringDecision(
                mission=mission,
                recommendation=recommendation,
                decision="hold",
                reason="Historical failures require additional verification before execution.",
            )

        if action == "review_historical_failures":
            return EngineeringDecision(
                mission=mission,
                recommendation=recommendation,
                decision="review",
                reason="Historical failures exist and require engineering review.",
            )

        if action == "no_historical_evidence":
            return EngineeringDecision(
                mission=mission,
                recommendation=recommendation,
                decision="review",
                reason="There is insufficient historical evidence for automatic progression.",
            )

        return EngineeringDecision(
            mission=mission,
            recommendation=recommendation,
            decision="proceed",
            reason="Historical evidence supports proceeding through the normal approval path.",
        )
