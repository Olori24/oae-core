from oae.capabilities.capability_dependency_graph import (
    CapabilityDependencyGraph,
)


def test_dependencies():

    graph = CapabilityDependencyGraph()

    assert graph.dependencies_for(
        "RBAC"
    ) == [
        "Authorization",
    ]

    assert graph.dependencies_for(
        "Docker Compose"
    ) == [
        "Docker",
    ]

    assert graph.dependencies_for(
        "Unknown"
    ) == []
