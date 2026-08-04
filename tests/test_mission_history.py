from oae.core.context import EngineeringContext
from oae.core.mission_history import MissionHistory


def test_mission_history():

    history = MissionHistory()

    context = EngineeringContext("Mission 060")
    context.success = True

    history.record(context)

    assert history.count() == 1
    assert history.all()[0]["mission"] == "Mission 060"
    assert history.all()[0]["success"] is True
