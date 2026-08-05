from oae.core.agent_selector import AgentSelector


def test_selector_creation():
    selector = AgentSelector()

    assert selector is not None


def test_register_agent():
    selector = AgentSelector()

    selector.register_agent(
        "Backend Engineer",
        ["python", "jwt"],
    )

    assert selector.engine.count() == 1


def test_select_agent():
    selector = AgentSelector()

    selector.register_agent(
        "Backend Engineer",
        ["python", "jwt"],
    )

    agent = selector.select("jwt")

    assert agent.name == "Backend Engineer"


def test_unknown_capability():
    selector = AgentSelector()

    selector.register_agent(
        "Backend Engineer",
        ["python"],
    )

    assert selector.select("kubernetes") is None


def test_least_busy_selected():
    selector = AgentSelector()

    selector.register_agent(
        "Backend Engineer",
        ["jwt"],
    )

    selector.register_agent(
        "Security Engineer",
        ["jwt"],
    )

    selector.workload.assign("Backend Engineer")

    agent = selector.select("jwt")

    assert agent.name == "Security Engineer"