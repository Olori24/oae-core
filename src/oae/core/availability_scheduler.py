from oae.core.agent_availability import AgentAvailability
from oae.core.workload_manager import WorkloadManager


class AvailabilityScheduler:
    """
    Selects the least busy available engineer.
    """

    def __init__(self):
        self.availability = AgentAvailability()
        self.workload = WorkloadManager()

    def register(self, agent):
        self.availability.register(agent)
        self.workload.register(agent)

    def select(self):
        available = [
            agent
            for agent in self.availability.agents()
            if self.availability.available(agent)
        ]

        if not available:
            return None

        return min(
            available,
            key=lambda a: self.workload.workload(a),
        )