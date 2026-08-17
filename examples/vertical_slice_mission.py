from pathlib import Path

from oae.core.vertical_slice_mission import VerticalSliceMission


if __name__ == "__main__":
    result = VerticalSliceMission().run(
        Path("generated/team-pulse"),
        name="TeamPulse",
        description=(
            "A developer team workspace where teams can submit engineering jobs, "
            "track job status, and inspect completed results from a dashboard."
        ),
    )
    print(result)
