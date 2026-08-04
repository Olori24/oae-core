from oae.repository.rollback import RollbackEngine


def test_rollback_missing_snapshot():

    rollback = RollbackEngine()

    assert rollback.rollback("missing") is False
