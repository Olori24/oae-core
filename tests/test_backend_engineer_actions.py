from oae.agents.backend_engineer_agent import (
    BackendEngineerAgent,
    BackendTask,
)


def test_backend_engineer_actions():

    agent = BackendEngineerAgent()

    task = BackendTask(
        title="Implement Logging",
        description="Add structured logging.",
    )

    actions = agent.actions(task)

    assert len(actions) == 3

    assert actions[0]["action"] == "analyze"

    assert actions[1]["action"] == "implement"

    assert actions[2]["action"] == "verify"
