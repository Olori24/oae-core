from oae.core.project_specification import ProjectSpecification
from oae.core.readme_generator import ReadmeGenerator


def test_generate(tmp_path):
    spec = ProjectSpecification(
        name="Demo",
        description="Demo project",
        language="Python",
        framework="FastAPI",
        database="SQLite",
        testing_framework="pytest",
    )

    generator = ReadmeGenerator()

    path = generator.generate(tmp_path, spec)

    assert path.exists()
    assert "Demo" in path.read_text()
