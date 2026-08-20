from oae.core.mission_dispatcher import MissionDispatcher


class RecoveryPriorityDispatcher:
    """
    Converts recovery decisions into prioritized missions
    and dispatches them through OAE's existing mission
    dispatcher.
    """

    FAILURE_PRIORITY = {
        "CRITICAL": 1,
        "HIGH": 2,
        "MEDIUM": 3,
        "LOW": 4,
        "UNKNOWN": 5,
    }

    def __init__(self):
        self.dispatcher = MissionDispatcher()

    def enqueue_recovery(self, recovery):
        if recovery.get("status") != "recovery_required":
            return None

        plan = recovery.get("plan")

        if not plan:
            return None

        risk = recovery.get("risk", {})

        risk_level = risk.get(
            "level",
            "UNKNOWN",
        )

        priority = self.FAILURE_PRIORITY.get(
            risk_level,
            self.FAILURE_PRIORITY["UNKNOWN"],
        )

        mission = plan.get("mission")

        if isinstance(mission, dict):
            objective = mission.get(
                "objective",
                mission.get(
                    "type",
                    "Recovery mission",
                ),
            )
        else:
            objective = str(mission)

        objective = str(objective)
        return self.dispatcher.queue.enqueue(
            objective,
            priority,
        )

    def dispatch(self):
        return self.dispatcher.dispatch()

    def pending(self):
        return self.dispatcher.queue.size()

    def scheduled_tasks(self):
        return self.dispatcher.scheduler.pending()
