"""
Snapshot Manager.

Defines the snapshot interface used by OAE.
"""


class SnapshotManager:
    """Manages repository and mission snapshots."""

    def __init__(self):
        self._snapshots = {}

    def create(self, target):
        """Create a snapshot."""

        snapshot_id = f"snapshot-{len(self._snapshots) + 1}"

        self._snapshots[snapshot_id] = target

        return snapshot_id

    def restore(self, snapshot_id):
        """Restore a snapshot."""

        return self._snapshots.get(snapshot_id)

    def list(self):
        """Return all snapshots."""

        return list(self._snapshots.keys())

    def delete(self, snapshot_id):
        """Delete a snapshot."""

        return self._snapshots.pop(snapshot_id, None) is not None
