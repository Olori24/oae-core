class MissionDependencyGraph:
    """
    Stores dependencies between missions.
    """

    def __init__(self):
        self._graph = {}

    def add_mission(self, mission):
        self._graph.setdefault(mission, [])

    def depends_on(self, mission, dependency):
        self.add_mission(mission)
        self.add_mission(dependency)

        self._graph[mission].append(dependency)

    def dependencies(self, mission):
        return self._graph.get(mission, [])

    def missions(self):
        return list(self._graph.keys())

    def count(self):
        return len(self._graph)