class RepositoryBacklogGenerator:
    """
    Converts repository diagnosis into engineering work items.
    """

    def generate(self, diagnosis):
        backlog = []

        if diagnosis["health"] < 90:
            backlog.append({
                "priority": "HIGH",
                "title": "Improve repository health",
            })

        if diagnosis["functions"] > 500:
            backlog.append({
                "priority": "HIGH",
                "title": "Refactor oversized codebase",
            })

        if diagnosis["classes"] > 100:
            backlog.append({
                "priority": "MEDIUM",
                "title": "Review architecture",
            })

        if not backlog:
            backlog.append({
                "priority": "LOW",
                "title": "Continue continuous improvement",
            })

        return backlog
