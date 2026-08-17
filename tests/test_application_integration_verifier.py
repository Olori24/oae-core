from oae.core.application_integration_verifier import ApplicationIntegrationVerifier
from oae.core.executable_application_generator import ExecutableApplicationGenerator
from oae.core.project_specification import ProjectSpecification


def spec():
    return ProjectSpecification(
        name="Integration Demo",
        description="Live integration target",
        language="Python",
        framework="FastAPI",
        database="SQLite",
        testing_framework="pytest",
    )


def test_health_endpoint_is_live(tmp_path):
    root = tmp_path / "demo"
    ExecutableApplicationGenerator().generate(root, spec())

    result = ApplicationIntegrationVerifier().verify(root, spec())

    assert result["passed"] is True
    assert result["status"] == "passed"
    assert '"status":"healthy"' in result["detail"].replace(" ", "")
