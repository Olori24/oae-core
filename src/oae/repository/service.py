"""
Repository Service.

Central access point for repository operations.
"""

from oae.repository.rollback import RollbackEngine
from oae.repository.scanner import RepositoryScanner
from oae.storage.snapshot import SnapshotManager


class RepositoryService:

    def __init__(self):

        self.scanner = RepositoryScanner()
        self.snapshots = SnapshotManager()
        self.rollback_engine = RollbackEngine()

    def scan(self, path):
        return self.scanner.scan(path)

    def create_snapshot(self, target):
        return self.snapshots.create(target)

    def restore_snapshot(self, snapshot_id):
        return self.snapshots.restore(snapshot_id)

    def rollback(self, snapshot_id):
        return self.rollback_engine.rollback(snapshot_id)

    def list_snapshots(self):
        return self.snapshots.list()

    def delete_snapshot(self, snapshot_id):
        return self.snapshots.delete(snapshot_id)
