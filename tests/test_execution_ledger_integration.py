from oae.core.engineering_ledger import EngineeringLedger
from oae.core.mission_execution_record import MissionExecutionRecord


def test_execution_record_can_be_recorded_in_ledger():
    ledger = EngineeringLedger()

    record = MissionExecutionRecord(
        "Fix authentication",
        engineer="Backend Engineer",
    )
    record.complete(
        execution={"passed": True},
        verification={"approved": True},
    )

    ledger.record(
        "MISSION_COMPLETED",
        str(record.to_dict()),
    )

    assert ledger.count() == 1

    entry = ledger.entries()[0]

    assert entry.event == "MISSION_COMPLETED"
    assert "Fix authentication" in entry.details
    assert "completed" in entry.details


def test_execution_engine_records_completion():
    from oae.core.event_bus import EventBus
    from oae.core.execution_engine import ExecutionEngine


    class DummyPipeline:
        def execute(self, context):
            return context


    engine = ExecutionEngine(
        EventBus(),
        DummyPipeline(),
    )

    engine.execute("Ledger Mission")

    assert engine.ledger.count() == 1

    entry = engine.ledger.entries()[0]

    assert entry.event == "MISSION_COMPLETED"
    assert "Ledger Mission" in entry.details


def test_execution_engine_records_failure():
    from oae.core.event_bus import EventBus
    from oae.core.execution_engine import ExecutionEngine


    class FailingPipeline:
        def execute(self, context):
            raise RuntimeError("verification failed")


    engine = ExecutionEngine(
        EventBus(),
        FailingPipeline(),
    )

    try:
        engine.execute("Failed Mission")
    except RuntimeError:
        pass

    assert engine.ledger.count() == 0
    assert engine.history.count() == 1
    assert engine.history.all()[0]["mission"] == "Failed Mission"
    assert engine.history.all()[0]["success"] is False


def test_execution_engine_records_recovery_required_failure():
    from oae.core.event_bus import EventBus
    from oae.core.execution_engine import ExecutionEngine
    from oae.core.autonomous_recovery_pipeline import (
        AutonomousRecoveryPipeline,
    )


    class FailingPipeline:
        def execute(self, context):
            return {
                "passed": False,
                "returncode": 1,
                "stdout": "",
                "stderr": "AssertionError: expected 1 got 2",
            }


    engine = ExecutionEngine(
        EventBus(),
        FailingPipeline(),
        recovery=AutonomousRecoveryPipeline(),
    )

    result = engine.execute("Fix authentication")

    assert result.success is False
    assert engine.ledger.count() == 1

    entry = engine.ledger.entries()[0]

    assert entry.event == "MISSION_FAILED"
    assert "Fix authentication" in entry.details
