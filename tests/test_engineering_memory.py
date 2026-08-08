from oae.core.engineering_ledger import EngineeringLedger
from oae.core.engineering_memory import EngineeringMemory


def test_creation():
    memory = EngineeringMemory(EngineeringLedger())

    assert memory is not None


def test_empty_memory():
    memory = EngineeringMemory(EngineeringLedger())

    assert memory.all_events() == []
    assert memory.count() == 0
    assert memory.latest() is None


def test_reads_all_events():
    ledger = EngineeringLedger()
    ledger.record("MISSION_STARTED", "Authentication")
    ledger.record("MISSION_COMPLETED", "Authentication verified")

    memory = EngineeringMemory(ledger)

    assert memory.count() == 2
    assert len(memory.all_events()) == 2


def test_filters_events():
    ledger = EngineeringLedger()
    ledger.record("MISSION_STARTED", "Authentication")
    ledger.record("MISSION_COMPLETED", "Authentication verified")
    ledger.record("MISSION_STARTED", "Database")

    memory = EngineeringMemory(ledger)

    assert memory.count("MISSION_STARTED") == 2
    assert memory.count("MISSION_COMPLETED") == 1


def test_latest_event():
    ledger = EngineeringLedger()
    ledger.record("MISSION_STARTED", "Authentication")
    ledger.record("MISSION_COMPLETED", "Authentication verified")

    memory = EngineeringMemory(ledger)

    latest = memory.latest()

    assert latest.event == "MISSION_COMPLETED"
    assert latest.details == "Authentication verified"


def test_successful_missions():
    ledger = EngineeringLedger()
    ledger.record("MISSION_COMPLETED", "Auth")
    ledger.record("MISSION_COMPLETED", "Database")
    ledger.record("MISSION_FAILED", "Payments")

    memory = EngineeringMemory(ledger)

    assert memory.successful_missions() == 2


def test_failed_missions():
    ledger = EngineeringLedger()
    ledger.record("MISSION_COMPLETED", "Auth")
    ledger.record("MISSION_FAILED", "Payments")
    ledger.record("MISSION_FAILED", "Database")

    memory = EngineeringMemory(ledger)

    assert memory.failed_missions() == 2


def test_success_rate():
    ledger = EngineeringLedger()
    ledger.record("MISSION_COMPLETED", "Auth")
    ledger.record("MISSION_COMPLETED", "Database")
    ledger.record("MISSION_FAILED", "Payments")

    memory = EngineeringMemory(ledger)

    assert memory.success_rate() == 2 / 3


def test_empty_success_rate():
    memory = EngineeringMemory(EngineeringLedger())

    assert memory.success_rate() == 0.0


def test_mission_events():
    ledger = EngineeringLedger()
    ledger.record("MISSION_STARTED", "Authentication")
    ledger.record("MISSION_COMPLETED", "Authentication verified")
    ledger.record("MISSION_STARTED", "Database")

    memory = EngineeringMemory(ledger)

    events = memory.mission_events("Authentication")

    assert len(events) == 2
    assert events[0].event == "MISSION_STARTED"
    assert events[1].event == "MISSION_COMPLETED"


def test_completed_mission_summary():
    ledger = EngineeringLedger()
    ledger.record("MISSION_STARTED", "Authentication")
    ledger.record("MISSION_COMPLETED", "Authentication verified")

    memory = EngineeringMemory(ledger)

    summary = memory.mission_summary("Authentication")

    assert summary["found"] is True
    assert summary["status"] == "completed"
    assert len(summary["events"]) == 2


def test_failed_mission_summary():
    ledger = EngineeringLedger()
    ledger.record("MISSION_STARTED", "Payments")
    ledger.record("MISSION_FAILED", "Payments failed")

    memory = EngineeringMemory(ledger)

    summary = memory.mission_summary("Payments")

    assert summary["found"] is True
    assert summary["status"] == "failed"


def test_running_mission_summary():
    ledger = EngineeringLedger()
    ledger.record("MISSION_STARTED", "Database")

    memory = EngineeringMemory(ledger)

    summary = memory.mission_summary("Database")

    assert summary["found"] is True
    assert summary["status"] == "running"


def test_unknown_mission_summary():
    memory = EngineeringMemory(EngineeringLedger())

    summary = memory.mission_summary("Unknown")

    assert summary["found"] is False
    assert summary["status"] == "unknown"
    assert summary["events"] == []
