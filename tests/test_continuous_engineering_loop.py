from oae.core.continuous_engineering_loop import (
    ContinuousEngineeringLoop,
)


def test_creation():
    loop = ContinuousEngineeringLoop()

    assert loop is not None


def test_single_cycle():
    loop = ContinuousEngineeringLoop()

    loop.register("Backend Engineer")
    loop.submit("Authentication", 5)

    result = loop.cycle()

    assert result["mission"] == "Authentication"


def test_run_all():
    loop = ContinuousEngineeringLoop()

    loop.register("Backend Engineer")

    loop.submit("One", 1)
    loop.submit("Two", 2)

    results = loop.run()

    assert len(results) == 2


def test_priority_order():
    loop = ContinuousEngineeringLoop()

    loop.register("Backend Engineer")

    loop.submit("Low", 1)
    loop.submit("High", 10)

    results = loop.run()

    assert results[0]["mission"] == "High"


def test_empty():
    loop = ContinuousEngineeringLoop()

    assert loop.run() == []