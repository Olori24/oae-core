from oae.core.multi_agent_dispatcher import MultiAgentDispatcher


def test_creation():
    dispatcher = MultiAgentDispatcher()

    assert dispatcher is not None


def test_register():
    dispatcher = MultiAgentDispatcher()

    dispatcher.register("Backend Engineer")

    dispatcher.add_mission("Authentication", 5)

    result = dispatcher.dispatch()

    assert result["engineer"] == "Backend Engineer"


def test_priority():
    dispatcher = MultiAgentDispatcher()

    dispatcher.register("Backend Engineer")

    dispatcher.add_mission("Low", 1)
    dispatcher.add_mission("High", 10)

    result = dispatcher.dispatch()

    assert result["mission"] == "High"


def test_empty_queue():
    dispatcher = MultiAgentDispatcher()

    assert dispatcher.dispatch() is None


def test_multiple_dispatches():
    dispatcher = MultiAgentDispatcher()

    dispatcher.register("Backend Engineer")

    dispatcher.add_mission("One", 1)
    dispatcher.add_mission("Two", 2)

    first = dispatcher.dispatch()
    second = dispatcher.dispatch()

    assert first["mission"] == "Two"
    assert second["mission"] == "One"