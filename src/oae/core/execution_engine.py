"""
OAE Execution Engine.
"""

from oae.core import events
from oae.core.context import EngineeringContext
from oae.core.mission_history import MissionHistory


class ExecutionEngine:
    """Executes engineering missions."""

    def __init__(self, event_bus, pipeline):
        self.event_bus = event_bus
        self.pipeline = pipeline
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
