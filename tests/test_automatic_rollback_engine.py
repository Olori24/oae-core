from oae.core.automatic_rollback_engine import (
    AutomaticRollbackEngine,
)


def test_rollback():
    engine = AutomaticRollbackEngine()

    result = engine.rollback("verification failed")

    assert result["rolled_back"] is True
    assert result["reason"] == "verification failed"


def test_structure():
    engine = AutomaticRollbackEngine()

    result = engine.rollback("error")

    assert "rolled_back" in result
    assert "reason" in result
