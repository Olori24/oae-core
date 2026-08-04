from oae.storage.snapshot import SnapshotManager


def test_snapshot_create():

    manager = SnapshotManager()

    snapshot = manager.create("repository")

    assert snapshot == "snapshot-1"


def test_snapshot_restore():

    manager = SnapshotManager()

    snapshot = manager.create("repository")

    assert manager.restore(snapshot) == "repository"


def test_snapshot_list():

    manager = SnapshotManager()

    manager.create("repo1")
    manager.create("repo2")

    assert len(manager.list()) == 2


def test_snapshot_delete():

    manager = SnapshotManager()

    snapshot = manager.create("repository")

    assert manager.delete(snapshot) is True

    assert manager.restore(snapshot) is None
