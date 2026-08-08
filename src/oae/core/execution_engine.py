"""
OAE Execution Engine.

Coordinates mission lifecycle, execution, verification,
recovery, and structured mission records.
"""

from oae.core import events
from oae.core.context import EngineeringContext
from oae.core.mission_execution_record import MissionExecutionRecord
from oae.core.mission_history import MissionHistory
from oae.core.engineering_ledger import EngineeringLedger


class ExecutionEngine:
    """Executes engineering missions."""

    def __init__(
        self,
        event_bus,
        pipeline,
        verifier=None,
        recovery=None,
        ledger=None,
    ):
        self.event_bus = event_bus
        self.pipeline = pipeline
        self.verifier = verifier
        self.recovery = recovery
        self.history = MissionHistory()
        self.ledger = ledger or EngineeringLedger()
        self.ledger = EngineeringLedger()

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

            execution_failed = (
                isinstance(result, dict)
                and result.get("passed") is False
            )

            if execution_failed:
                execution_context.success = False

            if self.verifier is not None:
                verification = self.verifier.verify(result)
                record.verification = verification

                if not verification["approved"]:
                    execution_context.success = False

                if (
                    execution_failed
                    or not verification["approved"]
                ):
                    if self.recovery is not None:
                        recovery_result = self.recovery.handle(
                            result,
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
            elif execution_failed:
                if self.recovery is not None:
                    recovery_result = self.recovery.handle(
                        result,
                        mission,
                    )
                    record.require_recovery(
                        recovery_result
                    )
                else:
                    record.fail(
                        execution=result,
                    )
            else:
                record.complete(
                    execution=result,
                    verification=None,
                )

            execution_context.complete()

            # Preserve the existing history contract.
            self.history.record(execution_context)

            if execution_context.success:
                self.ledger.record(
                    "MISSION_COMPLETED",
                    str(record.to_dict()),
                )

                self.event_bus.publish(
                    events.MISSION_COMPLETED,
                    execution_context,
                )
            else:
                self.ledger.record(
                    "MISSION_FAILED",
                    str(record.to_dict()),
                )

                self.event_bus.publish(
                    events.MISSION_FAILED,
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
