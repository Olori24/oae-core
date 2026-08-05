from oae.core.agent_registry import AgentRegistry


def test_registry_creation():
    registry = AgentRegistry()

    assert registry.count() == 0


def test_register_agent():
    registry = AgentRegistry()

    registry.register(
        "Backend Engineer",
        "backend",
    )

    assert registry.count() == 1


def test_exists():
    registry = AgentRegistry()

    registry.register(
        "QA Engineer",
        "qa",
    )

    assert registry.exists("QA Engineer")


def test_get_agent():
    registry = AgentRegistry()

    registry.register(
        "Security Engineer",
        "security",
    )

    agent = registry.get("Security Engineer")

    assert agent.role == "security"


def test_all_agents():
    registry = AgentRegistry()

    registry.register("Backend Engineer", "backend")
    registry.register("QA Engineer", "qa")
    registry.register("Security Engineer", "security")

    assert len(registry.all()) == 3