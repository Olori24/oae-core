from oae.core.architect_agent import ArchitecturePlan
from oae.core.backend_engineer_agent import BackendEngineerAgent
from oae.core.qa_engineer_agent import QAEngineerAgent


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


def test_qa_agent_creation():
    agent = QAEngineerAgent()

    assert agent is not None


def test_qa_report():
    agent = QAEngineerAgent()

    report = agent.validate(make_backend_task())

    assert report.objective == "Add JWT authentication"


def test_qa_contains_unit_tests():
    agent = QAEngineerAgent()

    report = agent.validate(make_backend_task())

    assert "Run unit tests" in report.tests_to_run


def test_qa_test_count():
    agent = QAEngineerAgent()

    report = agent.validate(make_backend_task())

    assert len(report.tests_to_run) == 4