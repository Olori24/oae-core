from oae.core.architect_agent import ArchitecturePlan
from oae.core.backend_engineer_agent import BackendEngineerAgent
from oae.core.devops_engineer_agent import DevOpsEngineerAgent


def make_backend_task():
    plan = ArchitecturePlan(
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

    backend = BackendEngineerAgent()

    return backend.implement(plan)


def test_devops_agent_creation():
    agent = DevOpsEngineerAgent()

    assert agent is not None


def test_deployment_plan():
    agent = DevOpsEngineerAgent()

    plan = agent.deploy(make_backend_task())

    assert plan.objective == "Add JWT authentication"


def test_deployment_steps():
    agent = DevOpsEngineerAgent()

    plan = agent.deploy(make_backend_task())

    assert "Deploy application" in plan.deployment_steps


def test_deployment_step_count():
    agent = DevOpsEngineerAgent()

    plan = agent.deploy(make_backend_task())

    assert len(plan.deployment_steps) == 5