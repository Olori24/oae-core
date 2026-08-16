from oae.core.project_specification import ProjectSpecification
from oae.core.pyproject_generator import PyprojectGenerator


def test_generate(tmp_path):
    spec = ProjectSpecification(
        name="Demo",
        description="Demo",
        language="Python",
        framework="FastAPI",
        database="SQLite",
        testing_framework="pytest",
    )

    path = PyprojectGenerator().generate(tmp_path, spec)

    assert path.exists()
