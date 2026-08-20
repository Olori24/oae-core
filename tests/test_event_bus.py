from oae.core import events
from oae.core.event_bus import EventBus


def test_event_bus():

    bus = EventBus()

    received = []

    def listener(data):
        received.append(data)

    bus.subscribe(events.MISSION_COMPLETED, listener)

    payload = {
        "mission": "Mission 054",
        "status": "completed",
    }

    bus.publish(events.MISSION_COMPLETED, payload)

    assert received == [payload]
