class WorkloadManager:
    """
    Tracks workload for registered AI engineers.
    """

    def __init__(self):
        self._workloads = {}

    def register(self, agent_name: str):
        self._workloads.setdefault(agent_name, 0)

    def assign(self, agent_name: str):
        self.register(agent_name)
        self._workloads[agent_name] += 1

    def complete(self, agent_name: str):
        if self._workloads.get(agent_name, 0) > 0:
            self._workloads[agent_name] -= 1

    def workload(self, agent_name: str):
        return self._workloads.get(agent_name, 0)

    def least_busy(self):
        if not self._workloads:
            return None

        return min(
            self._workloads,
            key=self._workloads.get,
        )