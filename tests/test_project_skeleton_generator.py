from oae.core.project_specification import ProjectSpecification
from oae.core.project_skeleton_generator import (
    ProjectSkeletonGenerator,
)


def test_generate(tmp_path):
    spec = ProjectSpecification(
        name="Opportunity Radar Africa",
        description="Funding discovery platform",
        language="Python",
        framework="FastAPI",
        database="PostgreSQL",
        testing_framework="pytest",
    )

    generator = ProjectSkeletonGenerator()

    project = generator.generate(tmp_path / "ora", spec)

    assert (project / "src").exists()
    assert (project / "tests").exists()
    assert (project / "docs").exists()
    assert (project / ".github").exists()


def test_readme_created(tmp_path):
    spec = ProjectSpecification(
        name="Demo",
        description="Demo Project",
        language="Python",
        framework="FastAPI",
        database="SQLite",
        testing_framework="pytest",
    )

    generator = ProjectSkeletonGenerator()

    project = generator.generate(tmp_path / "demo", spec)

    assert (project / "README.md").exists()
