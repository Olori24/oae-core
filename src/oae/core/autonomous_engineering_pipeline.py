from oae.core.autonomous_repository_pipeline import (
    AutonomousRepositoryPipeline,
)
from oae.core.continuous_engineering_loop import (
    ContinuousEngineeringLoop,
)


class AutonomousEngineeringPipeline:
    """
    Full autonomous engineering workflow.
    """

    def __init__(self):
        self.repository = AutonomousRepositoryPipeline()
        self.loop = ContinuousEngineeringLoop()

    def register(self, agent):
        self.loop.register(agent)

    def execute(self, repository_profile):
        missions = self.repository.process(repository_profile)

        for mission in missions:
            self.loop.submit(
                mission["title"],
                mission["priority"],
            )

        return self.loop.run()