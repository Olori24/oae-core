from oae.core.agent_availability import AgentAvailability
from oae.core.availability_scheduler import AvailabilityScheduler


def test_creation():
    scheduler = AvailabilityScheduler()

    assert scheduler is not None


def test_register():
    scheduler = AvailabilityScheduler()

    scheduler.register("Backend Engineer")

    assert scheduler.select() == "Backend Engineer"


def test_busy_agent():
    scheduler = AvailabilityScheduler()

    scheduler.register("Backend Engineer")
    scheduler.register("QA Engineer")

    scheduler.availability.set_state(
        "Backend Engineer",
        AgentAvailability.BUSY,
    )

    assert scheduler.select() == "QA Engineer"


def test_offline_agent():
    scheduler = AvailabilityScheduler()

    scheduler.register("Backend Engineer")
    scheduler.register("Security Engineer")

    scheduler.availability.set_state(
        "Backend Engineer",
        AgentAvailability.OFFLINE,
    )

    assert scheduler.select() == "Security Engineer"


def test_no_available_agents():
    scheduler = AvailabilityScheduler()

    scheduler.register("Backend Engineer")

    scheduler.availability.set_state(
        "Backend Engineer",
        AgentAvailability.MAINTENANCE,
    )

    assert scheduler.select() is None