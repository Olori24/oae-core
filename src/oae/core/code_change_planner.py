class CodeChangePlanner:
    """
    Determines which files should be modified for a mission.
    """

    def plan(self, mission, repository_files):
        affected = []

        for file in repository_files:
            if any(
                keyword in file.lower()
                for keyword in [
                    "auth",
                    "test",
                    "model",
                    "route",
                    "security",
                ]
            ):
                affected.append(file)

        return {
            "mission": mission,
            "files": affected,
        }
