from oae.core.mission_dispatcher import MissionDispatcher


def test_dispatcher_creation():
    dispatcher = MissionDispatcher()

    assert dispatcher is not None


def test_dispatch_empty():
    dispatcher = MissionDispatcher()

    assert dispatcher.dispatch() is None


def test_dispatch_mission():
    dispatcher = MissionDispatcher()

    dispatcher.queue.enqueue(
        "Implement JWT",
        2,
    )

    result = dispatcher.dispatch()

    assert result.dispatched is True
    assert result.objective == "Implement JWT"


def test_scheduler_receives_task():
    dispatcher = MissionDispatcher()

    dispatcher.queue.enqueue(
        "Implement JWT",
        1,
    )

    dispatcher.dispatch()

    assert len(dispatcher.scheduler.pending()) == 1


def test_queue_empty_after_dispatch():
    dispatcher = MissionDispatcher()

    dispatcher.queue.enqueue(
        "Implement JWT",
        1,
    )

    dispatcher.dispatch()

    assert dispatcher.queue.empty()