from oae.core.parallel_execution_planner import ParallelExecutionPlanner
from oae.core.workload_manager import WorkloadManager


class ResourceScheduler:
    """
    Matches executable missions to available engineering capacity.
    """

    def __init__(self):
        self.planner = ParallelExecutionPlanner()
        self.workload = WorkloadManager()

    def available_missions(self):
        return self.planner.executable()

    def least_busy_engineer(self):
        return self.workload.least_busy()