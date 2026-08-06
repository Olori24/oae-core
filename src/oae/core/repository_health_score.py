class RepositoryHealthScore:
    """
    Computes an overall engineering health score for a repository.
    """

    def calculate(
        self,
        security=100,
        testing=100,
        architecture=100,
        performance=100,
        documentation=100,
    ):
        overall = (
            security
            + testing
            + architecture
            + performance
            + documentation
        ) / 5

        return {
            "overall": round(overall),
            "security": security,
            "testing": testing,
            "architecture": architecture,
            "performance": performance,
            "documentation": documentation,
        }

    def recommendation(self, score):
        overall = score["overall"]

        if overall >= 90:
            return "Repository is in excellent health."

        if overall >= 75:
            return "Repository is healthy but has improvement opportunities."

        if overall >= 60:
            return "Repository requires engineering attention."

        return "Repository requires immediate intervention."