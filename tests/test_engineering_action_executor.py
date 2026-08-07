from oae.agents.engineering_action_executor import (
    EngineeringActionExecutor,
)


def test_execute_actions():

    executor = EngineeringActionExecutor()

    actions = [
        {
            "action": "analyze",
            "target": "Implement Logging",
        },
        {
            "action": "implement",
            "target": "Implement Logging",
        },
        {
            "action": "verify",
            "target": "Implement Logging",
        },
    ]

    results = executor.execute(actions)

    assert len(results) == 3

    assert results[0]["status"] == "completed"

    assert results[1]["status"] == "completed"

    assert results[2]["status"] == "completed"

    assert results[0]["action"] == "analyze"

    assert results[1]["action"] == "implement"

    assert results[2]["action"] == "verify"
