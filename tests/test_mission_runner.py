from oae.core.decision_engine import Decision
from oae.core.mission_runner import MissionRunner
from oae.security.request import ApprovalRequest


def test_high_confidence_mission():
    runner = MissionRunner()

    result = runner.run(
        action="refactor",
        target="src/oae/runtime.py",
        confidence=0.95,
    )

    assert isinstance(result, Decision)
    assert runner.ledger.count() == 2


def test_low_confidence_mission():
    runner = MissionRunner()

    result = runner.run(
        action="delete",
        target="src/oae/runtime.py",
        confidence=0.50,
    )

    assert isinstance(result, ApprovalRequest)
    assert runner.ledger.count() == 2