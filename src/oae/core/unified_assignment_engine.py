from oae.core.availability_scheduler import AvailabilityScheduler


class UnifiedAssignmentEngine:
    """
    Produces the best engineer assignment.
    """

    def __init__(self):
        self.scheduler = AvailabilityScheduler()

    def register(self, agent):
        self.scheduler.register(agent)

    def assign(self, mission):
        engineer = self.scheduler.select()

        if engineer is None:
            return None

        return {
            "mission": mission,
            "engineer": engineer,
        }