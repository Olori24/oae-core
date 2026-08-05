from oae.core.workload_manager import WorkloadManager


class ExecutionFeedback:
    """
    Updates engineer workload after mission completion.
    """

    def __init__(self):
        self.workload_manager = WorkloadManager()

    def register(self, agent):
        self.workload_manager.register(agent)

    def assign(self, agent):
        self.workload_manager.assign(agent)

    def complete(self, agent):
        self.workload_manager.complete(agent)

    def workload(self, agent):
        return self.workload_manager.workload(agent)