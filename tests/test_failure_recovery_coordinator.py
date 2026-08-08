from oae.core.failure_recovery_coordinator import (
    FailureRecoveryCoordinator,
)


def test_success_requires_no_recovery():

    coordinator = FailureRecoveryCoordinator()

    result = coordinator.recover(
        {
            "passed": True,
            "returncode": 0,
            "stdout": "tests passed",
            "stderr": "",
        },
        "Implement authentication",
    )

    assert result["status"] == "no_recovery_required"
    assert result["failure_type"] == "NO_FAILURE"


def test_failure_requires_recovery():

    coordinator = FailureRecoveryCoordinator()

    result = coordinator.recover(
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


def test_recovery_contains_risk():

    coordinator = FailureRecoveryCoordinator()

    result = coordinator.recover(
        {
            "passed": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "SyntaxError: invalid syntax",
        },
        "Fix parser",
    )

    assert result["risk"]["action"] == "modify"
    assert result["risk"]["level"] == "MEDIUM"
    assert result["risk"]["score"] == 60


def test_recovery_contains_plan():

    coordinator = FailureRecoveryCoordinator()

    result = coordinator.recover(
        {
            "passed": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "ImportError: missing module",
        },
        "Fix imports",
    )

    assert result["plan"]["mission"] == "Fix imports"

    assert (
        result["plan"]["steps"][0]
        == "Locate affected files"
    )

    assert (
        result["plan"]["steps"][-1]
        == "Report result"
    )
