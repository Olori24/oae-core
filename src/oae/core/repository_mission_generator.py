class RepositoryMissionGenerator:
    """
    Generates engineering missions from repository findings.
    """

    def generate(self, findings):
        missions = []

        for finding in findings:
            missions.append(
                {
                    "title": finding,
                    "priority": 5,
                }
            )

        return missions