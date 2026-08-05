from oae.core.mission_lifecycle import (
    Mission,
    MissionLifecycleManager,
    MissionStatus,
)


def test_manager_creation():
    manager = MissionLifecycleManager()

    assert manager is not None


def test_new_mission():
    mission = Mission("Implement JWT")

    assert mission.status == MissionStatus.CREATED


def test_planning():
    manager = MissionLifecycleManager()

    mission = Mission("Implement JWT")

    manager.advance(
        mission,
        MissionStatus.PLANNING,
    )

    assert mission.status == MissionStatus.PLANNING


def test_architecture():
    manager = MissionLifecycleManager()

    mission = Mission("Implement JWT")

    manager.advance(
        mission,
        MissionStatus.ARCHITECTURE,
    )

    assert mission.status == MissionStatus.ARCHITECTURE


def test_completed():
    manager = MissionLifecycleManager()

    mission = Mission("Implement JWT")

    manager.advance(
        mission,
        MissionStatus.COMPLETED,
    )

    assert mission.status == MissionStatus.COMPLETED