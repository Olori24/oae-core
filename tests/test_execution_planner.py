from oae.core.execution_planner import ExecutionPlanner


def test_planner_creation():
    planner = ExecutionPlanner()

    assert planner is not None


def test_single_ready_mission():
    planner = ExecutionPlanner()

    planner.resolver.graph.add_mission(
        "Backend API"
    )

    ready = planner.ready_missions()

    assert ready == ["Backend API"]


def test_blocked_mission_not_ready():
    planner = ExecutionPlanner()

    planner.resolver.graph.depends_on(
        "Deployment",
        "Backend API",
    )

    ready = planner.ready_missions()

    assert "Deployment" not in ready


def test_ready_after_completion():
    planner = ExecutionPlanner()

    planner.resolver.graph.depends_on(
        "Deployment",
        "Backend API",
    )

    planner.resolver.complete(
        "Backend API"
    )

    ready = planner.ready_missions()

    assert "Deployment" in ready


def test_multiple_ready_missions():
    planner = ExecutionPlanner()

    planner.resolver.graph.add_mission(
        "Documentation"
    )

    planner.resolver.graph.add_mission(
        "Backend API"
    )

    ready = planner.ready_missions()

    assert len(ready) == 2