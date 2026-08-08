from oae.core.mission_execution_record import MissionExecutionRecord


def test_creation():
    record = MissionExecutionRecord("Fix authentication")

    assert record.mission == "Fix authentication"
    assert record.status == "pending"


def test_complete():
    record = MissionExecutionRecord("Fix authentication")

    result = record.complete(
        execution={"passed": True},
        verification={"approved": True},
    )

    assert result is record
    assert record.status == "completed"
    assert record.execution["passed"] is True
    assert record.verification["approved"] is True


def test_fail():
    record = MissionExecutionRecord("Fix authentication")

    record.fail(
        execution={"passed": False},
        verification={"approved": False},
    )

    assert record.status == "failed"


def test_recovery():
    record = MissionExecutionRecord("Fix authentication")

    record.require_recovery(
        {"failure_type": "TEST_FAILURE"}
    )

    assert record.status == "recovery_required"
    assert record.recovery["failure_type"] == "TEST_FAILURE"


def test_to_dict():
    record = MissionExecutionRecord(
        "Fix authentication",
        engineer="Backend Engineer",
    )

    data = record.to_dict()

    assert data["mission"] == "Fix authentication"
    assert data["engineer"] == "Backend Engineer"
    assert data["status"] == "pending"
    assert data["execution"] is None
    assert data["verification"] is None
    assert data["recovery"] is None
