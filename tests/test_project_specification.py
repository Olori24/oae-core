from oae.core.project_specification import ProjectSpecification


def test_project_specification():
    spec = ProjectSpecification(
        name="Opportunity Radar Africa",
        description="Funding discovery platform",
        language="Python",
        framework="FastAPI",
        database="PostgreSQL",
        testing_framework="pytest",
    )

    assert spec.name == "Opportunity Radar Africa"
    assert spec.framework == "FastAPI"
    assert spec.database == "PostgreSQL"


def test_defaults():
    spec = ProjectSpecification(
        name="Demo",
        description="Demo",
        language="Python",
        framework="FastAPI",
        database="SQLite",
        testing_framework="pytest",
    )

    assert spec.docker is True
    assert spec.ci is True
