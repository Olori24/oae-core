from oae.core.engineering_state_manager import EngineeringStateManager


def test_creation():
    manager = EngineeringStateManager()

    assert manager is not None


def test_set_get():
    manager = EngineeringStateManager()

    manager.set("active_missions", 5)

    assert manager.get("active_missions") == 5


def test_increment():
    manager = EngineeringStateManager()

    manager.increment("completed_missions")
    manager.increment("completed_missions")

    assert manager.get("completed_missions") == 2


def test_snapshot():
    manager = EngineeringStateManager()

    snapshot = manager.snapshot()

    assert isinstance(snapshot, dict)


def test_snapshot_contains_defaults():
    manager = EngineeringStateManager()

    snapshot = manager.snapshot()

    assert "active_missions" in snapshot
    assert "completed_missions" in snapshot