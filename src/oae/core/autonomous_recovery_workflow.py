from oae.core.failure_recovery_coordinator import (
    FailureRecoveryCoordinator,
)
from oae.core.recovery_mission_bridge import (
    RecoveryMissionBridge,
)
from oae.core.recovery_priority_dispatcher import (
    RecoveryPriorityDispatcher,
)


class AutonomousRecoveryWorkflow:
    """
    Coordinates failure detection, recovery planning,
    mission injection, prioritization, and dispatch.
    """

    def __init__(self):
        self.recovery_coordinator = FailureRecoveryCoordinator()
        self.mission_bridge = RecoveryMissionBridge()
        self.priority_dispatcher = RecoveryPriorityDispatcher()

    def recover(self, execution_result, mission):
        """
        Convert an execution failure into a dispatched
        recovery mission.
        """

        recovery = self.recovery_coordinator.recover(
            execution_result,
            mission,
        )

        if recovery.get("status") != "recovery_required":
            return {
                "status": "no_recovery_required",
                "recovery": recovery,
                "missions": [],
                "dispatch": None,
            }

        missions = self.mission_bridge.create_missions(
            recovery
        )

        for mission_data in missions:
            self.priority_dispatcher.enqueue_recovery(
                {
                    "status": "recovery_required",
                    "risk": recovery.get("risk", {}),
                    "plan": {
                        "mission": mission_data["mission"],
                        "steps": mission_data["steps"],
                    },
                }
            )

        dispatch = self.priority_dispatcher.dispatch()

        return {
            "status": "recovery_dispatched",
            "recovery": recovery,
            "missions": missions,
            "dispatch": dispatch,
        }
