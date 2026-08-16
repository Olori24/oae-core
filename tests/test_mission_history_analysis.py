from oae.core.mission_history import MissionHistory


class Context:
    def __init__(self, mission, success=True):
        self.mission = mission
        self.success = success


def test_history_analysis_empty():
    history = MissionHistory()

    result = history.analyze()

    assert result["total"] == 0
    assert result["completed"] == 0
    assert result["failed"] == 0


def test_history_analysis():
    history = MissionHistory()

    history.record(Context("Mission A", True))
    history.record(Context("Mission B", False))

    result = history.analyze()

    assert result["total"] == 2
    assert result["completed"] == 1
    assert result["failed"] == 1
    assert result["success_rate"] == 0.5
