from oae.core.project_specification import ProjectSpecification
from oae.core.application_scaffold_generator import (
    ApplicationScaffoldGenerator,
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

    ApplicationScaffoldGenerator().generate(tmp_path, spec)

    assert (tmp_path / "src" / "main.py").exists()
    assert (tmp_path / "src" / "api" / "health.py").exists()
    assert (tmp_path / "src" / "config" / "settings.py").exists()
    assert (tmp_path / "tests" / "test_health.py").exists()
