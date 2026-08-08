from oae.core.failure_recovery_coordinator import (
    FailureRecoveryCoordinator,
)
from oae.core.recovery_mission_bridge import (
    RecoveryMissionBridge,
)
from oae.core.mission_dispatcher import (
    MissionDispatcher,
)


class AutonomousRecoveryPipeline:
    """
    Coordinates autonomous failure recovery from classification
    through mission creation and dispatch.
    """

    def __init__(self):
        self.recovery = FailureRecoveryCoordinator()
        self.bridge = RecoveryMissionBridge()
        self.dispatcher = MissionDispatcher()

    def handle(self, execution_result, mission):
        recovery = self.recovery.recover(
            execution_result,
            mission,
        )

        missions = self.bridge.create_missions(
            recovery
        )

        for injected in missions:
            objective = injected["mission"]

            if isinstance(objective, dict):
                objective = objective.get(
                    "objective",
                    objective.get("type", str(objective)),
                )

            self.dispatcher.queue.enqueue(
                objective,
                1,
            )

        return {
            **recovery,
            "missions": missions,
        }

    def dispatch(self):
        return self.dispatcher.dispatch()
