from oae.core.mission_injection_engine import (
    MissionInjectionEngine,
)


class AutonomousEngineeringLoop:
    """
    Coordinates continuous autonomous engineering execution.
    """

    def __init__(self):
        self.injector = MissionInjectionEngine()

    def execute(self, recovery):
        missions = self.injector.inject(recovery)

        return {
            "missions": missions,
            "queued": len(missions),
        }
