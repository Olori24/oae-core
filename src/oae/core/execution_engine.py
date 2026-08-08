"""
OAE Execution Engine.

Coordinates mission lifecycle, execution, verification,
recovery, and structured mission records.
"""

from oae.core import events
from oae.core.context import EngineeringContext
from oae.core.mission_execution_record import MissionExecutionRecord
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
        record = MissionExecutionRecord(mission)

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

            # Preserve the EngineeringContext contract.
            execution_context = (
                result
                if isinstance(result, EngineeringContext)
                else context
            )

            record.execution = result

            if isinstance(result, dict):
                record.engineer = result.get("engineer")

            if self.verifier is not None:
                verification = self.verifier.verify(result)
                record.verification = verification

                if not verification["approved"]:
                    execution_context.success = False

                    if self.recovery is not None:
                        recovery_result = self.recovery.handle(
                            verification,
                            mission,
                        )
                        record.require_recovery(
                            recovery_result
                        )
                    else:
                        record.fail(
                            execution=result,
                            verification=verification,
                        )
                else:
                    record.complete(
                        execution=result,
                        verification=verification,
                    )
            else:
                record.complete(
                    execution=result,
                    verification=None,
                )

            execution_context.complete()

            # Preserve the existing history contract.
            self.history.record(execution_context)

            self.event_bus.publish(
                events.MISSION_COMPLETED,
                execution_context,
            )

            return execution_context

        except Exception as exc:
            context.success = False
            context.error = exc
            context.complete()

            record.fail(
                execution=exc,
            )

            self.history.record(context)

            self.event_bus.publish(
                events.MISSION_FAILED,
                exc,
            )

            raise
