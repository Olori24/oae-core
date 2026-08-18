from pathlib import Path

from oae.core.vertical_slice_mission import VerticalSliceMission


MISSION = {
    "name": "TeamPulse",
    "description": (
        "A multi-user developer workspace where authenticated teams can create "
        "engineering jobs, track their status, and inspect completed results."
    ),
}


if __name__ == "__main__":
    result = VerticalSliceMission().run(
        Path("generated/teampulse"),
        name=MISSION["name"],
        description=MISSION["description"],
    )
    print("TeamPulse mission result:")
    print(result)
