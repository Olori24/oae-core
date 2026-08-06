class EngineeringJournal:
    """
    Records autonomous engineering activities.
    """

    def __init__(self):
        self._entries = []

    def record(
        self,
        mission,
        engineer,
        outcome,
        risk="LOW",
        confidence=0.90,
    ):
        self._entries.append(
            {
                "mission": mission,
                "engineer": engineer,
                "outcome": outcome,
                "risk": risk,
                "confidence": confidence,
            }
        )

    def entries(self):
        return list(self._entries)

    def latest(self):
        if not self._entries:
            return None

        return self._entries[-1]

    def total(self):
        return len(self._entries)