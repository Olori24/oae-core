"""
Rollback Engine.

Restores repositories from snapshots.
"""

from oae.storage.snapshot import SnapshotManager


class RollbackEngine:
    """Handles repository recovery."""

    def __init__(self):
        self.snapshots = SnapshotManager()

    def rollback(self, snapshot_id):
        """Restore a repository snapshot."""

        restored = self.snapshots.restore(snapshot_id)

        if restored is None:
            return False

        return True
