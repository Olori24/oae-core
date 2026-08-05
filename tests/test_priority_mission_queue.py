from oae.core.priority_mission_queue import PriorityMissionQueue


def test_queue_creation():
    queue = PriorityMissionQueue()

    assert queue.empty()


def test_enqueue():
    queue = PriorityMissionQueue()

    queue.enqueue("Implement JWT", 3)

    assert queue.size() == 1


def test_priority_order():
    queue = PriorityMissionQueue()

    queue.enqueue("Documentation", 5)
    queue.enqueue("Security Patch", 1)
    queue.enqueue("Production Bug", 2)

    first = queue.dequeue()
    second = queue.dequeue()
    third = queue.dequeue()

    assert first.objective == "Security Patch"
    assert second.objective == "Production Bug"
    assert third.objective == "Documentation"


def test_peek():
    queue = PriorityMissionQueue()

    queue.enqueue("Feature", 3)
    queue.enqueue("Critical Bug", 1)

    assert queue.peek().objective == "Critical Bug"


def test_empty_after_dequeue():
    queue = PriorityMissionQueue()

    queue.enqueue("Mission", 1)

    queue.dequeue()

    assert queue.empty()