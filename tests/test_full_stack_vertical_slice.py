from oae.core.full_stack_vertical_slice import FullStackVerticalSlice
from oae.core.project_specification import ProjectSpecification


def test_full_stack_vertical_slice(tmp_path):
    specification = ProjectSpecification(
        name="OAE Vertical Slice",
        description="A complete generated application slice",
        language="Python",
        framework="FastAPI",
        database="SQLite",
        testing_framework="pytest",
    )

    result = FullStackVerticalSlice().execute(tmp_path / "app", specification)

    assert result["application"] == "OAE Vertical Slice"
    assert result["readiness_score"] == 100
    assert result["verified"] is True
    assert result["blockers"] == []
    assert result["verification"]["execution"]["backend"]["passed"] is True
    assert result["verification"]["execution"]["frontend"]["passed"] is True
