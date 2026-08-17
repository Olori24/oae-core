from oae.core.application_quality_gate import ApplicationQualityGate
from oae.core.project_bootstrap_orchestrator import ProjectBootstrapOrchestrator
from oae.core.project_specification import ProjectSpecification


def spec():
    return ProjectSpecification(
        name="Quality Gate Demo",
        description="Generated quality gate target",
        language="Python",
        framework="FastAPI",
        database="SQLite",
        testing_framework="pytest",
    )


def test_quality_gate_accepts_verified_application(tmp_path):
    root = tmp_path / "demo"
    ProjectBootstrapOrchestrator().bootstrap(root, spec())

    result = ApplicationQualityGate().evaluate(root, spec())

    assert result["status"] == "production_candidate"
    assert result["verified"] is True
    assert result["readiness_score"] == 100
    assert result["blockers"] == []


def test_quality_gate_reports_blocker(tmp_path):
    root = tmp_path / "demo"
    ProjectBootstrapOrchestrator().bootstrap(root, spec())
    (root / "src" / "main.py").unlink()

    result = ApplicationQualityGate().evaluate(root, spec())

    assert result["status"] == "blocked"
    assert result["verified"] is False
    assert result["blockers"]
