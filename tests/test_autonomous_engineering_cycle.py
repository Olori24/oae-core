from oae.core.autonomous_engineering_cycle import (
    AutonomousEngineeringCycle,
)


def test_creation():
    cycle = AutonomousEngineeringCycle()

    assert cycle is not None


def test_empty_repository():
    cycle = AutonomousEngineeringCycle()

    assert cycle.execute([]) == []


def test_single_execution():
    cycle = AutonomousEngineeringCycle()

    cycle.register("Backend Engineer")

    results = cycle.execute(["auth.py"])

    assert len(results) == 1


def test_completed_state():
    cycle = AutonomousEngineeringCycle()

    cycle.register("Backend Engineer")

    cycle.execute(["auth.py"])

    assert cycle.state.get("completed_missions") == 1


def test_multiple_execution():
    cycle = AutonomousEngineeringCycle()

    cycle.register("Backend Engineer")

    results = cycle.execute([
        "auth.py",
        "models.py",
        "routes.py",
    ])

    assert len(results) == 3