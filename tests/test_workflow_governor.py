from oae.core.mission_lifecycle import MissionStatus
from oae.core.workflow_governor import WorkflowGovernor


def test_governor_creation():
    governor = WorkflowGovernor()

    assert governor is not None


def test_valid_transition():
    governor = WorkflowGovernor()

    assert governor.is_valid(
        MissionStatus.CREATED,
        MissionStatus.PLANNING,
    )


def test_invalid_transition():
    governor = WorkflowGovernor()

    assert not governor.is_valid(
        MissionStatus.CREATED,
        MissionStatus.DEPLOYMENT,
    )


def test_completed_has_no_next():
    governor = WorkflowGovernor()

    assert not governor.is_valid(
        MissionStatus.COMPLETED,
        MissionStatus.PLANNING,
    )


def test_security_to_deployment():
    governor = WorkflowGovernor()

    assert governor.is_valid(
        MissionStatus.SECURITY,
        MissionStatus.DEPLOYMENT,
    )
