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

    assert len(actions) == 4

    assert actions[0]["operation"] == "create_file"

    assert actions[1]["operation"] == "modify_file"

    assert actions[2]["operation"] == "run_tests"

    assert actions[3]["operation"] == "commit_changes"
