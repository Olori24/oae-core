from oae.core.failure_recovery_coordinator import (
    FailureRecoveryCoordinator,
)
from oae.core.recovery_mission_bridge import (
    RecoveryMissionBridge,
)


class AutonomousRecoveryPipeline:
    """
    Converts failed execution results into controlled recovery missions.
    """

    def __init__(self):
        self.coordinator = FailureRecoveryCoordinator()
        self.bridge = RecoveryMissionBridge()
        self._missions = []

    def handle(self, execution_result, mission):
        """
        Analyze an execution result and create recovery missions when needed.
        """
        recovery = self.coordinator.recover(
            execution_result,
            mission,
        )

        if recovery["status"] == "no_recovery_required":
            self._missions = []
            return {
                "status": "no_recovery_required",
                "failure_type": recovery["failure_type"],
                "missions": [],
            }

        self._missions = self.bridge.create_missions(
            recovery
        )

        return {
            "status": "recovery_required",
            "failure_type": recovery["failure_type"],
            "risk": recovery["risk"],
            "plan": recovery["plan"],
            "missions": self._missions,
        }

    def dispatch(self):
        """
        Dispatch the next pending recovery mission.
        """
        if not self._missions:
            return None

        for mission in self._missions:
            if mission.get("status") == "pending":
                mission["status"] = "dispatched"

                return type(
                    "RecoveryDispatch",
                    (),
                    {
                        "dispatched": True,
                        "objective": mission["mission"],
                        "mission": mission,
                    },
                )()

        return None
