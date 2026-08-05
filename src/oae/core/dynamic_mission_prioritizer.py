class DynamicMissionPrioritizer:
    """
    Prioritizes engineering missions.
    """

    def __init__(self):
        self._missions = []

    def add(self, mission, priority=0):
        self._missions.append(
            {
                "mission": mission,
                "priority": priority,
            }
        )

    def next(self):
        if not self._missions:
            return None

        highest = max(
            self._missions,
            key=lambda m: m["priority"],
        )

        self._missions.remove(highest)

        return highest["mission"]

    def pending(self):
        return len(self._missions)