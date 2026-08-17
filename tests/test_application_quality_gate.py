from oae.core.application_quality_gate import ApplicationQualityGate
from oae.core.project_bootstrap_orchestrator import ProjectBootstrapOrchestrator
from oae.core.project_specification import ProjectSpecification


def spec():
    return ProjectSpecification(
        name="Quality Gate Demo",
        description="Quality gate target",
        language="Python",
        framework="FastAPI",
        database="SQLite",
        testing_framework="pytest",
    )


class FakeVerifier:
    def __init__(self, status="verified"):
        self.status = status
        self.execute_frontend_build = None

    def verify(self, root, specification, execute_frontend_build=False):
        self.execute_frontend_build = execute_frontend_build
        passed = self.status == "verified"
        return {
            "status": self.status,
            "readiness": {"score": 100},
            "checks": [
                {"name": "backend", "passed": passed, "detail": "ok" if passed else "failed"}
            ],
            "execution": None,
        }


def test_quality_gate_executes_frontend_build():
    verifier = FakeVerifier()

    result = ApplicationQualityGate(verifier=verifier).evaluate(
        "/tmp/demo", spec()
    )

    assert result["status"] == "production_candidate"
    assert verifier.execute_frontend_build is True


def test_quality_gate_reports_blocker():
    verifier = FakeVerifier(status="failed")

    result = ApplicationQualityGate(verifier=verifier).evaluate(
        "/tmp/demo", spec()
    )

    assert result["status"] == "blocked"
    assert result["verified"] is False
    assert result["blockers"] == ["failed"]
