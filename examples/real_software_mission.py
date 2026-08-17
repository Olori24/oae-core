"""A real developer-style mission for exercising OAE's generation and verification spine."""

from pathlib import Path

from oae.core.full_stack_vertical_slice import FullStackVerticalSlice
from oae.core.project_specification import ProjectSpecification


MISSION = ProjectSpecification(
    name="TeamPulse",
    description=(
        "A small SaaS for development teams to create engineering jobs, "
        "track their status, and inspect the result from a shared dashboard."
    ),
    language="Python",
    framework="FastAPI",
    database="SQLite",
    testing_framework="pytest",
)


def run(output_dir=".oae-demo/teampulse"):
    result = FullStackVerticalSlice().execute(Path(output_dir), MISSION)
    print(f"Application: {result['application']}")
    print(f"Status: {result['status']}")
    print(f"Readiness: {result['readiness_score']}%")
    print(f"Verified: {result['verified']}")
    if result["blockers"]:
        print("Blockers:")
        for blocker in result["blockers"]:
            print(f"- {blocker}")
    return result


if __name__ == "__main__":
    run()
