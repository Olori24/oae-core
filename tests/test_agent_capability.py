from oae.core.agent_capability import AgentCapabilityEngine


def test_engine_creation():
    engine = AgentCapabilityEngine()

    assert engine.count() == 0


def test_register_agent():
    engine = AgentCapabilityEngine()

    engine.register(
        "Backend Engineer",
        ["python", "fastapi"],
    )

    assert engine.count() == 1


def test_exists():
    engine = AgentCapabilityEngine()

    engine.register(
        "QA Engineer",
        ["testing"],
    )

    assert engine.exists("QA Engineer")


def test_find_capability():
    engine = AgentCapabilityEngine()

    engine.register(
        "Backend Engineer",
        ["python", "jwt"],
    )

    result = engine.find("jwt")

    assert len(result) == 1
    assert result[0].name == "Backend Engineer"


def test_unknown_capability():
    engine = AgentCapabilityEngine()

    engine.register(
        "Backend Engineer",
        ["python"],
    )

    result = engine.find("kubernetes")

    assert result == []