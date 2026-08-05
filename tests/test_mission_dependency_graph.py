from oae.core.mission_dependency_graph import MissionDependencyGraph


def test_graph_creation():
    graph = MissionDependencyGraph()

    assert graph.count() == 0


def test_add_mission():
    graph = MissionDependencyGraph()

    graph.add_mission("Backend API")

    assert graph.count() == 1


def test_add_dependency():
    graph = MissionDependencyGraph()

    graph.depends_on(
        "Integration Tests",
        "Backend API",
    )

    deps = graph.dependencies("Integration Tests")

    assert deps == ["Backend API"]


def test_multiple_dependencies():
    graph = MissionDependencyGraph()

    graph.depends_on(
        "Deployment",
        "Backend API",
    )

    graph.depends_on(
        "Deployment",
        "Security Scan",
    )

    deps = graph.dependencies("Deployment")

    assert len(deps) == 2


def test_list_missions():
    graph = MissionDependencyGraph()

    graph.add_mission("Mission A")
    graph.add_mission("Mission B")

    assert len(graph.missions()) == 2