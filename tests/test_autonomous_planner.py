from oae.core.autonomous_planner import AutonomousPlanner


def test_plan_creation():
    planner = AutonomousPlanner()

    plan = planner.plan("Add JWT authentication")

    assert plan.objective == "Add JWT authentication"


def test_default_task_count():
    planner = AutonomousPlanner()

    plan = planner.plan("Any task")

    assert len(plan.tasks) == 9


def test_first_task():
    planner = AutonomousPlanner()

    plan = planner.plan("Anything")

    assert plan.tasks[0] == "Inspect repository"


def test_last_task():
    planner = AutonomousPlanner()

    plan = planner.plan("Anything")

    assert plan.tasks[-1] == "Record engineering ledger"