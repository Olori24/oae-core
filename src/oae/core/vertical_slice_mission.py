from pathlib import Path

from oae.core.full_stack_vertical_slice import FullStackVerticalSlice
from oae.core.project_specification import ProjectSpecification


class VerticalSliceMission:
    """Run a product specification through OAE's complete generation gate."""

    def __init__(self, executor=None):
        self.executor = executor or FullStackVerticalSlice()

    def run(self, root, *, name, description, language="Python", framework="FastAPI", database="SQLite", testing_framework="pytest"):
        specification = ProjectSpecification(
            name=name,
            description=description,
            language=language,
            framework=framework,
            database=database,
            testing_framework=testing_framework,
        )
        result = self.executor.execute(Path(root), specification)
        return {
            "mission": name,
            "application": name,
            "status": result["status"],
            "verified": result["verified"],
            "readiness_score": result["readiness_score"],
            "blockers": result["blockers"],
            "root": result["root"],
            "contract": result.get("contract"),
            "verification": result.get("verification"),
        }
