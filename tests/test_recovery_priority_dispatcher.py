from oae.core.recovery_priority_dispatcher import (
    RecoveryPriorityDispatcher,
)


def recovery(
    mission="Fix authentication",
    level="MEDIUM",
):
    return {
        "status": "recovery_required",
        "failure_type": "TEST_FAILURE",
        "risk": {
            "level": level,
            "score": 60,
        },
        "plan": {
            "mission": mission,
            "steps": [
                "Locate affected files",
                "Analyze implementation",
                "Apply modification",
                "Run verification",
                "Report result",
            ],
        },
    }


def test_no_recovery_is_not_enqueued():

    dispatcher = RecoveryPriorityDispatcher()

    result = dispatcher.enqueue_recovery(
        {
            "status": "no_recovery_required",
            "failure_type": "NO_FAILURE",
        }
    )

    assert result is None
    assert dispatcher.pending() == 0


def test_recovery_is_enqueued():

    dispatcher = RecoveryPriorityDispatcher()

    result = dispatcher.enqueue_recovery(
        recovery()
    )

    assert result is not None
    assert result.objective == "Fix authentication"
    assert result.priority == 3
    assert dispatcher.pending() == 1


def test_high_risk_gets_higher_priority():

    dispatcher = RecoveryPriorityDispatcher()

    dispatcher.enqueue_recovery(
        recovery(
            mission="Repair production parser",
            level="HIGH",
        )
    )

    mission = dispatcher.dispatch()

    assert mission.dispatched is True
    assert mission.objective == "Repair production parser"


def test_dispatch_schedules_task():

    dispatcher = RecoveryPriorityDispatcher()

    dispatcher.enqueue_recovery(
        recovery(
            mission="Repair authentication",
        )
    )

    result = dispatcher.dispatch()

    assert result.dispatched is True

    tasks = dispatcher.scheduled_tasks()

    assert len(tasks) == 1
    assert tasks[0].agent == "Chief Architect"
    assert tasks[0].task == "Repair authentication"


def test_priority_order():

    dispatcher = RecoveryPriorityDispatcher()

    dispatcher.enqueue_recovery(
        recovery(
            mission="Medium repair",
            level="MEDIUM",
        )
    )

    dispatcher.enqueue_recovery(
        recovery(
            mission="High repair",
            level="HIGH",
        )
    )

    first = dispatcher.dispatch()
    second = dispatcher.dispatch()

    assert first.objective == "High repair"
    assert second.objective == "Medium repair"
