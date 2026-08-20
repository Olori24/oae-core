from oae.core.autonomous_recovery_pipeline import (
    AutonomousRecoveryPipeline,
)


def test_success_requires_no_recovery():
    pipeline = AutonomousRecoveryPipeline()

    result = pipeline.handle(
        {
            "passed": True,
            "returncode": 0,
            "stdout": "551 passed",
            "stderr": "",
        },
        "Implement authentication",
    )

    assert result["status"] == "no_recovery_required"
    assert result["missions"] == []


def test_failure_creates_recovery_mission():
    pipeline = AutonomousRecoveryPipeline()

    result = pipeline.handle(
        {
            "passed": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "AssertionError: expected 1 got 2",
        },
        "Fix authentication",
    )

    assert result["status"] == "recovery_required"
    assert result["failure_type"] == "TEST_FAILURE"
    assert len(result["missions"]) == 1
    assert result["missions"][0]["status"] == "pending"


def test_failure_mission_contains_steps():
    pipeline = AutonomousRecoveryPipeline()

    result = pipeline.handle(
        {
            "passed": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "SyntaxError: invalid syntax",
        },
        "Fix parser",
    )

    mission = result["missions"][0]

    assert mission["mission"] == "Fix parser"
    assert mission["steps"][0] == "Locate affected files"
    assert mission["steps"][-1] == "Report result"


def test_recovery_mission_can_be_dispatched():
    pipeline = AutonomousRecoveryPipeline()

    pipeline.handle(
        {
            "passed": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "ImportError: missing module",
        },
        "Fix imports",
    )

    dispatched = pipeline.dispatch()

    assert dispatched is not None
    assert dispatched.dispatched is True
    assert dispatched.objective == "Fix imports"
