from oae.core.application_verification_engine import ApplicationVerificationEngine
from oae.core.project_bootstrap_orchestrator import ProjectBootstrapOrchestrator
from oae.core.project_specification import ProjectSpecification


def spec():
    return ProjectSpecification(
        name="Verification Demo",
        description="Generated verification target",
        language="Python",
        framework="FastAPI",
        database="SQLite",
        testing_framework="pytest",
    )


def test_generated_application_is_executable(tmp_path):
    root = tmp_path / "demo"
    ProjectBootstrapOrchestrator().bootstrap(root, spec())

    result = ApplicationVerificationEngine().verify(
        root,
        spec(),
        execute_frontend_build=False,
    )

    assert result["status"] == "verified"
    assert result["execution"]["backend"]["passed"] is True
    assert result["execution"]["backend"]["returncode"] == 0
    assert result["execution"]["frontend"]["passed"] is True
    assert result["execution"]["frontend"]["status"] == "ready"


def test_verification_blocks_missing_contract(tmp_path):
    root = tmp_path / "demo"
    ProjectBootstrapOrchestrator().bootstrap(root, spec())
    (root / "src" / "main.py").unlink()

    result = ApplicationVerificationEngine().verify(root, spec())

    assert result["status"] == "blocked"
    assert result["execution"] is None
