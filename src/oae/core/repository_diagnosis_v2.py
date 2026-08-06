class RepositoryDiagnosisV2:
    """
    Generates engineering metrics from repository intelligence.
    """

    def diagnose(self, intelligence):
        knowledge = intelligence["knowledge"]

        files = len(knowledge)

        functions = sum(
            len(item.get("functions", []))
            for item in knowledge.values()
        )

        classes = sum(
            len(item.get("classes", []))
            for item in knowledge.values()
        )

        health = 100

        if functions > 500:
            health -= 10

        if classes > 100:
            health -= 5

        return {
            "files": files,
            "functions": functions,
            "classes": classes,
            "health": health,
        }
