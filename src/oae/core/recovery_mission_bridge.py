from oae.core.mission_injection_engine import (
    MissionInjectionEngine,
)


class RecoveryMissionBridge:
    """
    Converts a failure recovery decision into
    executable missions using OAE's existing
    mission injection infrastructure.
    """

    def __init__(self):

        self.injector = MissionInjectionEngine()

    def create_missions(self, recovery):

        if recovery.get("status") != "recovery_required":
            return []

        plan = recovery.get("plan")

        if not plan:
            return []

        return self.injector.inject(
            {
                "plans": [
                    plan,
                ]
            }
        )
