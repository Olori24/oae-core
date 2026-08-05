from oae.core.mission_queue import MissionQueue


def test_queue_creation():
    queue = MissionQueue()

    assert queue.empty()


def test_enqueue():
    queue = MissionQueue()

    queue.enqueue("Implement JWT")

    assert queue.size() == 1


def test_peek():
    queue = MissionQueue()

    queue.enqueue("Mission A")

    assert queue.peek().objective == "Mission A"


def test_dequeue():
    queue = MissionQueue()

    queue.enqueue("Mission A")

    mission = queue.dequeue()

    assert mission.objective == "Mission A"
    assert queue.empty()


def test_fifo_order():
    queue = MissionQueue()

    queue.enqueue("Mission A")
    queue.enqueue("Mission B")

    first = queue.dequeue()
    second = queue.dequeue()

    assert first.objective == "Mission A"
    assert second.objective == "Mission B"