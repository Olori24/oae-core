class AutonomousFixPlanner:
    """
    Creates an execution plan for an engineering mission.
    """

    def plan(self, mission):
        return {
            "mission": mission,
            "steps": [
                "Locate affected files",
                "Analyze implementation",
                "Apply modification",
                "Run verification",
                "Report result",
            ],
        }