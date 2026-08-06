class RepositoryDiagnosisEngine:
    """
    Produces a high-level diagnosis from repository knowledge.
    """

    def diagnose(self, knowledge_graph):
        total_files = len(knowledge_graph)

        total_functions = sum(
            len(data.get("functions", []))
            for data in knowledge_graph.values()
        )

        total_classes = sum(
            len(data.get("classes", []))
            for data in knowledge_graph.values()
        )

        return {
            "files": total_files,
            "functions": total_functions,
            "classes": total_classes,
            "health": "GOOD" if total_files else "EMPTY",
        }