from oae.core.dependency_resolver import DependencyResolver


class ExecutionPlanner:
    """
    Determines which missions are ready to execute.
    """

    def __init__(self):
        self.resolver = DependencyResolver()

    def ready_missions(self):
        ready = []

        for mission in self.resolver.graph.missions():
            if self.resolver.ready(mission):
                ready.append(mission)

        return ready