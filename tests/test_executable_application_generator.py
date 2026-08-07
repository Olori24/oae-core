from oae.core.project_specification import ProjectSpecification
from oae.core.executable_application_generator import (
    ExecutableApplicationGenerator,
)


def test_generate(tmp_path):
    spec = ProjectSpecification(
        name="Opportunity Radar Africa",
        description="Demo",
        language="Python",
        framework="FastAPI",
        database="PostgreSQL",
        testing_framework="pytest",
    )

    main = ExecutableApplicationGenerator().generate(
        tmp_path,
        spec,
    )

    assert main.exists()
    assert (tmp_path / "src" / "api" / "health.py").exists()
