from oae.core.recovery_mission_bridge import (
    RecoveryMissionBridge,
)


def test_no_recovery_creates_no_missions():

    bridge = RecoveryMissionBridge()

    result = bridge.create_missions(
        {
            "status": "no_recovery_required",
            "failure_type": "NO_FAILURE",
        }
    )

    assert result == []


def test_recovery_creates_mission():

    bridge = RecoveryMissionBridge()

    recovery = {
        "status": "recovery_required",
        "failure_type": "TEST_FAILURE",
        "plan": {
            "mission": "Fix authentication tests",
            "steps": [
                "Locate affected files",
                "Analyze implementation",
                "Apply modification",
                "Run verification",
                "Report result",
            ],
        },
    }

    result = bridge.create_missions(recovery)

    assert len(result) == 1

    assert result[0]["status"] == "pending"

    assert (
        result[0]["mission"]
        == "Fix authentication tests"
    )


def test_recovery_preserves_steps():

    bridge = RecoveryMissionBridge()

    recovery = {
        "status": "recovery_required",
        "failure_type": "SYNTAX_ERROR",
        "plan": {
            "mission": "Fix parser",
            "steps": [
                "Locate affected files",
                "Analyze implementation",
                "Apply modification",
                "Run verification",
                "Report result",
            ],
        },
    }

    result = bridge.create_missions(recovery)

    assert result[0]["steps"] == recovery["plan"]["steps"]
