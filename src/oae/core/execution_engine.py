"""
OAE Execution Engine.

Coordinates mission lifecycle, execution, verification,
and optional autonomous recovery.
"""

from oae.core import events
from oae.core.context import EngineeringContext
from oae.core.mission_history import MissionHistory


class ExecutionEngine:
    """Executes engineering missions."""

    def __init__(
        self,
        event_bus,
        pipeline,
        verifier=None,
        recovery=None,
    ):
        self.event_bus = event_bus
        self.pipeline = pipeline
        self.verifier = verifier
        self.recovery = recovery
        self.history = MissionHistory()

    def execute(self, mission):
        context = EngineeringContext(mission)

        self.event_bus.publish(
            events.MISSION_CREATED,
            context,
        )

        self.event_bus.publish(
            events.MISSION_STARTED,
            context,
        )

        try:
            result = self.pipeline.execute(context)

            if self.verifier is not None:
                verification = self.verifier.verify(result)

                if not verification["approved"]:
                    if self.recovery is not None:
                        recovery_result = self.recovery.handle(
                            verification,
                            mission,
                        )

                        result = {
                            "execution": result,
                            "verification": verification,
                            "recovery": recovery_result,
                        }

                    context.success = False
                    self.history.record(context)

                    self.event_bus.publish(
                        events.MISSION_FAILED,
                        result,
                    )

                    return result

            self.history.record(result)

            self.event_bus.publish(
                events.MISSION_COMPLETED,
                result,
            )

            return result

        except Exception as exc:
            context.success = False

            self.history.record(context)

            self.event_bus.publish(
                events.MISSION_FAILED,
                exc,
            )

            raise
