from oae.core.dependency_resolver import DependencyResolver


def test_resolver_creation():
    resolver = DependencyResolver()

    assert resolver is not None


def test_ready_without_dependencies():
    resolver = DependencyResolver()

    resolver.graph.add_mission("Backend API")

    assert resolver.ready("Backend API")


def test_not_ready_until_dependency_completed():
    resolver = DependencyResolver()

    resolver.graph.depends_on(
        "Deployment",
        "Backend API",
    )

    assert resolver.ready("Deployment") is False


def test_ready_after_dependency_completed():
    resolver = DependencyResolver()

    resolver.graph.depends_on(
        "Deployment",
        "Backend API",
    )

    resolver.complete("Backend API")

    assert resolver.ready("Deployment")


def test_multiple_dependencies():
    resolver = DependencyResolver()

    resolver.graph.depends_on(
        "Release",
        "Backend API",
    )

    resolver.graph.depends_on(
        "Release",
        "Security Scan",
    )

    resolver.complete("Backend API")

    assert resolver.ready("Release") is False

    resolver.complete("Security Scan")

    assert resolver.ready("Release")