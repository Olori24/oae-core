from oae.core.mission_dependency_graph import MissionDependencyGraph


class DependencyResolver:
    """
    Resolves whether missions are ready for execution.
    """

    def __init__(self):
        self.graph = MissionDependencyGraph()
        self.completed = set()

    def complete(self, mission):
        self.completed.add(mission)

    def ready(self, mission):
        dependencies = self.graph.dependencies(mission)

        return all(
            dependency in self.completed
            for dependency in dependencies
        )