from oae.core.resource_scheduler import ResourceScheduler


class IntelligentAssignment:
    """
    Assigns executable missions to available engineers.
    """

    def __init__(self):
        self.scheduler = ResourceScheduler()

    def next_missions(self):
        return self.scheduler.available_missions()

    def next_engineer(self):
        return self.scheduler.least_busy_engineer()

    def assignment(self):
        missions = self.next_missions()
        engineer = self.next_engineer()

        if not missions or engineer is None:
            return None

        return {
            "mission": missions[0],
            "engineer": engineer,
        }