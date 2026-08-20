from oae.core.autonomous_recovery_workflow import (
    AutonomousRecoveryWorkflow,
)


def test_creation():

    workflow = AutonomousRecoveryWorkflow()

    assert workflow is not None


def test_successful_execution_requires_no_recovery():

    workflow = AutonomousRecoveryWorkflow()

    result = workflow.recover(
        {
            "passed": True,
            "returncode": 0,
        },
        "Run repository tests",
    )

    assert result["status"] == "no_recovery_required"
    assert result["missions"] == []
    assert result["dispatch"] is None


def test_failed_execution_creates_recovery():

    workflow = AutonomousRecoveryWorkflow()

    result = workflow.recover(
        {
            "passed": False,
            "returncode": 1,
            "stderr": "AssertionError",
        },
        "Fix authentication",
    )

    assert result["status"] == "recovery_dispatched"

    assert len(result["missions"]) == 1

    assert (
        result["dispatch"].dispatched
        is True
    )


def test_recovery_mission_is_scheduled():

    workflow = AutonomousRecoveryWorkflow()

    workflow.recover(
        {
            "passed": False,
            "returncode": 1,
            "stderr": "AssertionError",
        },
        "Fix authentication",
    )

    tasks = (
        workflow.priority_dispatcher
        .scheduled_tasks()
    )

    assert len(tasks) == 1

    assert (
        tasks[0].agent
        == "Chief Architect"
    )

    assert (
        tasks[0].task
        == "Fix authentication"
    )
