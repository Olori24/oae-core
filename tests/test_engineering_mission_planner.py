from oae.core.engineering_mission_planner import (
    EngineeringMissionPlanner,
)


def test_creation():
    planner = EngineeringMissionPlanner()

    assert planner is not None


def test_default_plan():
    planner = EngineeringMissionPlanner()

    diagnosis = {
        "functions": 3,
        "classes": 2,
        "health": "GOOD",
    }

    missions = planner.plan(diagnosis)

    assert len(missions) == 1
    assert missions[0]["priority"] == "LOW"


def test_large_repository():
    planner = EngineeringMissionPlanner()

    diagnosis = {
        "functions": 150,
        "classes": 10,
        "health": "GOOD",
    }

    missions = planner.plan(diagnosis)

    assert missions[0]["priority"] == "HIGH"


def test_architecture_review():
    planner = EngineeringMissionPlanner()

    diagnosis = {
        "functions": 20,
        "classes": 70,
        "health": "GOOD",
    }

    missions = planner.plan(diagnosis)

    assert any(
        mission["title"] == "Review architecture"
        for mission in missions
    )


def test_bad_health():
    planner = EngineeringMissionPlanner()

    diagnosis = {
        "functions": 10,
        "classes": 5,
        "health": "POOR",
    }

    missions = planner.plan(diagnosis)

    assert any(
        mission["title"] == "Investigate repository health"
        for mission in missions
    )