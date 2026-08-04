from oae.core.context import EngineeringContext
from oae.core.history_service import HistoryService


def test_history_service():

    history = HistoryService()

    history.clear()

    context = EngineeringContext("Mission 061")
    context.success = True

    history.record(context)

    assert history.count() == 1
    assert history.all()[0]["mission"] == "Mission 061"
    assert history.all()[0]["success"] is True
