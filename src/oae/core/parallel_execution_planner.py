from oae.core.execution_planner import ExecutionPlanner


class ParallelExecutionPlanner:
    """
    Finds all missions that are currently executable.
    """

    def __init__(self):
        self.planner = ExecutionPlanner()

    def executable(self):
        return self.planner.ready_missions()