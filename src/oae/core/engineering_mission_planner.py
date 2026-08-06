class EngineeringMissionPlanner:
    """
    Generates engineering missions from repository diagnosis.
    """

    def plan(self, diagnosis):
        missions = []

        if diagnosis["functions"] > 100:
            missions.append(
                {
                    "title": "Refactor large codebase",
                    "priority": "HIGH",
                }
            )

        if diagnosis["classes"] > 50:
            missions.append(
                {
                    "title": "Review architecture",
                    "priority": "MEDIUM",
                }
            )

        if diagnosis["health"] != "GOOD":
            missions.append(
                {
                    "title": "Investigate repository health",
                    "priority": "HIGH",
                }
            )

        if not missions:
            missions.append(
                {
                    "title": "Continue continuous improvement",
                    "priority": "LOW",
                }
            )

        return missions