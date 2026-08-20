from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from oae.api.workspace_models import WorkspaceManifest, WorkspaceManifestEntry, WorkspacePurpose

NOW = datetime(2026, 8, 20, tzinfo=timezone.utc)
SHA = "a" * 64


def entry(**overrides):
    values = {
        "id": "entry-1",
        "relative_path": "src/main.py",
        "object_key": "tenant/t-1/workspace/w-1/src/main.py",
        "sha256": SHA,
        "size_bytes": 19,
        "content_type": "text/x-python",
        "created_at": NOW,
    }
    values.update(overrides)
    return WorkspaceManifestEntry(**values)


def manifest(**overrides):
    values = {
        "workspace_id": "w-1",
        "tenant_id": "t-1",
        "repository_id": "r-1",
        "source_revision_id": "rev-1",
        "purpose": WorkspacePurpose.SOURCE,
        "storage_uri": "s3://oae-workspaces/tenant/t-1/workspace/w-1",
        "manifest_sha256": SHA,
        "entries": [entry()],
        "created_at": NOW,
        "retention_expires_at": NOW + timedelta(days=30),
    }
    values.update(overrides)
    return WorkspaceManifest(**values)


def test_workspace_manifest_calculates_total_size():
    result = manifest(entries=[entry(size_bytes=19), entry(id="entry-2", relative_path="README.md", object_key="tenant/t-1/workspace/w-1/README.md", size_bytes=7)])

    assert result.total_size_bytes == 26


@pytest.mark.parametrize("path", ["../secrets.txt", "/etc/passwd", "src\\main.py", "."])
def test_manifest_entry_rejects_unsafe_paths(path):
    with pytest.raises(ValidationError, match="traversal-safe"):
        entry(relative_path=path)


def test_workspace_manifest_rejects_duplicate_paths():
    with pytest.raises(ValidationError, match="unique relative paths"):
        manifest(entries=[entry(), entry(id="entry-2")])


def test_workspace_manifest_rejects_embedded_storage_credentials():
    with pytest.raises(ValidationError, match="without embedded credentials"):
        manifest(storage_uri="s3://access:secret@oae-workspaces/tenant/t-1")
