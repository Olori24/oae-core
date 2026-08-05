from oae.core.architect_agent import ArchitecturePlan
from oae.core.backend_engineer_agent import BackendEngineerAgent


def make_plan():
    return ArchitecturePlan(
        objective="Add JWT authentication",
        language="Python",
        framework="FastAPI",
        tasks=[
            "Inspect repository",
            "Analyze repository context",
            "Analyze dependencies",
            "Assess impact",
            "Assess risk",
            "Request approval if needed",
            "Execute changes",
            "Run tests",
            "Record engineering ledger",
        ],
    )


def test_backend_agent_creation():
    agent = BackendEngineerAgent()

    assert agent is not None


def test_backend_task_creation():
    agent = BackendEngineerAgent()

    task = agent.implement(make_plan())

    assert task.objective == "Add JWT authentication"


def test_backend_adds_steps():
    agent = BackendEngineerAgent()

    task = agent.implement(make_plan())

    assert "Implement backend code" in task.implementation_steps
    assert "Verify backend implementation" in task.implementation_steps


def test_backend_step_count():
    agent = BackendEngineerAgent()

    task = agent.implement(make_plan())

    assert len(task.implementation_steps) == 11