from oae.agents.backend_engineer_agent import (
    BackendEngineerAgent,
    BackendTask,
)


def test_backend_engineer_plan():

    agent = BackendEngineerAgent()

    task = BackendTask(
        title="Implement Logging",
        description="Add structured logging.",
    )

    plan = agent.plan(task)

    assert plan["task"] == "Implement Logging"

    assert plan["owner"] == "Backend Engineer"

    assert plan["status"] == "planned"
