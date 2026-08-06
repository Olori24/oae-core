from oae.core.autonomous_engineering_cycle import (
    AutonomousEngineeringCycle,
)


class AutonomousRepositorySupervisor:
    """
    Supervises autonomous engineering for a repository.
    """

    def __init__(self):
        self.cycle = AutonomousEngineeringCycle()

    def register(self, agent):
        self.cycle.register(agent)

    def supervise(self, repository_profile):
        return self.cycle.execute(repository_profile)