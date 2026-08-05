from oae.core.parallel_execution_planner import ParallelExecutionPlanner


def test_planner_creation():
    planner = ParallelExecutionPlanner()

    assert planner is not None


def test_single_executable():
    planner = ParallelExecutionPlanner()

    planner.planner.resolver.graph.add_mission(
        "Backend API"
    )

    executable = planner.executable()

    assert executable == ["Backend API"]


def test_blocked_mission():
    planner = ParallelExecutionPlanner()

    planner.planner.resolver.graph.depends_on(
        "Deployment",
        "Backend API",
    )

    executable = planner.executable()

    assert "Deployment" not in executable


def test_dependency_completed():
    planner = ParallelExecutionPlanner()

    planner.planner.resolver.graph.depends_on(
        "Deployment",
        "Backend API",
    )

    planner.planner.resolver.complete(
        "Backend API"
    )

    executable = planner.executable()

    assert "Deployment" in executable


def test_multiple_parallel():
    planner = ParallelExecutionPlanner()

    planner.planner.resolver.graph.add_mission(
        "Documentation"
    )

    planner.planner.resolver.graph.add_mission(
        "Security Scan"
    )

    planner.planner.resolver.graph.add_mission(
        "Backend API"
    )

    executable = planner.executable()

    assert len(executable) == 3