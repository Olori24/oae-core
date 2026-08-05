from oae.core.agent_availability import AgentAvailability


def test_creation():
    availability = AgentAvailability()

    assert availability is not None


def test_register():
    availability = AgentAvailability()

    availability.register("Backend Engineer")

    assert availability.state("Backend Engineer") == AgentAvailability.IDLE


def test_set_busy():
    availability = AgentAvailability()

    availability.register("Backend Engineer")

    availability.set_state(
        "Backend Engineer",
        AgentAvailability.BUSY,
    )

    assert availability.state("Backend Engineer") == AgentAvailability.BUSY


def test_available():
    availability = AgentAvailability()

    availability.register("QA Engineer")

    assert availability.available("QA Engineer")


def test_not_available():
    availability = AgentAvailability()

    availability.register("QA Engineer")

    availability.set_state(
        "QA Engineer",
        AgentAvailability.OFFLINE,
    )

    assert availability.available("QA Engineer") is False