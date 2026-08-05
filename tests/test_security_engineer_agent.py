from oae.core.architect_agent import ArchitecturePlan
from oae.core.backend_engineer_agent import BackendEngineerAgent
from oae.core.security_engineer_agent import SecurityEngineerAgent


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


def test_security_agent_creation():
    agent = SecurityEngineerAgent()

    assert agent is not None


def test_security_review():
    agent = SecurityEngineerAgent()

    review = agent.review(make_backend_task())

    assert review.objective == "Add JWT authentication"


def test_security_approval():
    agent = SecurityEngineerAgent()

    review = agent.review(make_backend_task())

    assert review.approved is True


def test_security_findings():
    agent = SecurityEngineerAgent()

    review = agent.review(make_backend_task())

    assert len(review.findings) == 3