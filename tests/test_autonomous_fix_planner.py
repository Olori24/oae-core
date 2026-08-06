from oae.core.autonomous_fix_planner import (
    AutonomousFixPlanner,
)


def test_creation():
    planner = AutonomousFixPlanner()

    assert planner is not None


def test_plan_contains_steps():
    planner = AutonomousFixPlanner()

    plan = planner.plan("Fix authentication")

    assert len(plan["steps"]) == 5


def test_plan_contains_mission():
    planner = AutonomousFixPlanner()

    plan = planner.plan("Fix authentication")

    assert plan["mission"] == "Fix authentication"


def test_first_step():
    planner = AutonomousFixPlanner()

    plan = planner.plan("Any")

    assert plan["steps"][0] == "Locate affected files"


def test_last_step():
    planner = AutonomousFixPlanner()

    plan = planner.plan("Any")

    assert plan["steps"][-1] == "Report result"