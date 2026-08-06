from oae.core.engineering_memory_engine import (
    EngineeringMemoryEngine,
)


def test_remember():
    engine = EngineeringMemoryEngine()

    engine.remember("planner", "successful")

    assert engine.recall("planner") == "successful"


def test_forget():
    engine = EngineeringMemoryEngine()

    engine.remember("planner", "successful")
    engine.forget("planner")

    assert engine.recall("planner") is None


def test_unknown():
    engine = EngineeringMemoryEngine()

    assert engine.recall("unknown") is None


def test_all():
    engine = EngineeringMemoryEngine()

    engine.remember("a", 1)
    engine.remember("b", 2)

    memory = engine.all()

    assert memory["a"] == 1
    assert memory["b"] == 2
