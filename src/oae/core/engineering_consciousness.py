class EngineeringConsciousness:
    """
    Produces explainable engineering decisions.
    """

    def evaluate(self, mission):
        return {
            "objective": mission,
            "reason": self._reason(mission),
            "risk": self._risk(mission),
            "confidence": self._confidence(mission),
            "rollback_required": True,
            "verification_plan": self._verification(mission),
        }

    def _reason(self, mission):
        return f"Mission '{mission}' improves repository quality."

    def _risk(self, mission):
        mission = mission.lower()

        if "security" in mission:
            return "HIGH"

        if "dependency" in mission:
            return "MEDIUM"

        return "LOW"

    def _confidence(self, mission):
        mission = mission.lower()

        if "security" in mission:
            return 0.95

        if "test" in mission:
            return 0.92

        return 0.90

    def _verification(self, mission):
        return [
            "Run unit tests",
            "Run integration tests",
            "Validate repository state",
        ]