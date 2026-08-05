from oae.core.dynamic_mission_prioritizer import (
    DynamicMissionPrioritizer,
)


def test_creation():
    prioritizer = DynamicMissionPrioritizer()

    assert prioritizer is not None


def test_add():
    prioritizer = DynamicMissionPrioritizer()

    prioritizer.add("Mission A", 1)

    assert prioritizer.pending() == 1


def test_highest_priority():
    prioritizer = DynamicMissionPrioritizer()

    prioritizer.add("Low", 1)
    prioritizer.add("Medium", 5)
    prioritizer.add("High", 10)

    assert prioritizer.next() == "High"


def test_pending_after_pop():
    prioritizer = DynamicMissionPrioritizer()

    prioritizer.add("Mission", 3)

    prioritizer.next()

    assert prioritizer.pending() == 0


def test_empty():
    prioritizer = DynamicMissionPrioritizer()

    assert prioritizer.next() is None