from pathlib import Path

import pytest

from oae.api.workspace_manager import (
    PinnedRepositoryRevision,
    PinnedRevisionNotFound,
    WorkspaceQuotaExceeded,
)
from oae.api.workspace_manager import (
    WorkspaceManager as ApiWorkspaceManager,
)
from oae.api.workspace_models import WorkspacePurpose, WorkspaceState
from oae.core.workspace_manager import WorkspaceManager as LegacyWorkspaceManager


def test_workspace_creation(tmp_path):
    manager = LegacyWorkspaceManager(tmp_path)

    workspace = manager.create_workspace(
        "opportunity-radar-africa"
    )

    assert workspace.exists()


class FakeMaterializer:
    def __init__(self):
        self.materialized_commit = None

    def materialize(self, revision, target: Path):
        self.materialized_commit = revision.commit_sha
        target.mkdir(parents=True)
        (target / "src").mkdir()
        (target / "src" / "main.py").write_text("print('ready')\n", encoding="utf-8")
        (target / "README.md").write_text("workspace\n", encoding="utf-8")
        (target / ".git").mkdir()
        (target / ".git" / "config").write_text("excluded", encoding="utf-8")


class FakeRepository:
    def __init__(self, revision=None, quota_error=False):
        self.revision = revision
        self.quota_error = quota_error
        self.reservations = []
        self.ready = []
        self.failed = []

    def get_pinned_revision(self, tenant_id, repository_id, revision_id):
        return self.revision

    def reserve(self, record, entries):
        if self.quota_error:
            raise WorkspaceQuotaExceeded("Workspace byte quota exceeded for this tenant.")
        self.reservations.append((record, entries))

    def mark_ready(self, tenant_id, workspace_id, ready_at):
        self.ready.append((tenant_id, workspace_id, ready_at))

    def mark_failed(self, tenant_id, workspace_id, failure_code):
        self.failed.append((tenant_id, workspace_id, failure_code))


@pytest.fixture
def revision():
    return PinnedRepositoryRevision(
        tenant_id="tenant-1",
        repository_id="repository-1",
        revision_id="revision-1",
        clone_url="https://github.com/example/repository.git",
        commit_sha="a" * 40,
    )


def test_manager_provisions_manifest_from_pinned_revision(tmp_path, revision):
    materializer = FakeMaterializer()
    repository = FakeRepository(revision)
    manager = ApiWorkspaceManager(root=tmp_path, repository=repository, materializer=materializer)

    record, manifest = manager.provision("tenant-1", "repository-1", "revision-1")

    assert materializer.materialized_commit == "a" * 40
    assert record.state == WorkspaceState.READY
    assert record.file_count == 2
    assert record.size_bytes == manifest.total_size_bytes
    assert {entry.relative_path for entry in manifest.entries} == {"README.md", "src/main.py"}
    assert len(repository.reservations) == 1
    assert len(repository.ready) == 1
    workspace_root = tmp_path / "tenant" / "tenant-1" / "workspace" / record.id
    assert (workspace_root / "manifest.json").exists()
    assert not (workspace_root / "content" / ".git").exists()


def test_manager_rejects_unknown_pinned_revision(tmp_path):
    manager = ApiWorkspaceManager(root=tmp_path, repository=FakeRepository(), materializer=FakeMaterializer())

    with pytest.raises(PinnedRevisionNotFound):
        manager.provision("tenant-1", "repository-1", "revision-1")


def test_manager_cleans_staging_when_quota_reservation_fails(tmp_path, revision):
    manager = ApiWorkspaceManager(
        root=tmp_path,
        repository=FakeRepository(revision, quota_error=True),
        materializer=FakeMaterializer(),
    )

    with pytest.raises(WorkspaceQuotaExceeded):
        manager.provision("tenant-1", "repository-1", "revision-1", WorkspacePurpose.EXECUTION)

    assert not any((tmp_path / ".staging").glob("*"))
    assert not (tmp_path / "tenant" / "tenant-1" / "workspace").exists()
