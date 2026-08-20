"""Typed contracts for durable repository workspaces and their file manifests."""

from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath

from pydantic import BaseModel, Field, field_validator, model_validator


class WorkspacePurpose(StrEnum):
    SOURCE = "source"
    EXECUTION = "execution"
    OUTPUT = "output"
    REVIEW = "review"


class WorkspaceState(StrEnum):
    PROVISIONING = "provisioning"
    READY = "ready"
    DELETING = "deleting"
    DELETED = "deleted"
    FAILED = "failed"


def _safe_relative_path(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not value
        or value == "."
        or path.is_absolute()
        or ".." in path.parts
        or "." in path.parts
        or "\\" in value
    ):
        raise ValueError("path must be a non-empty, traversal-safe POSIX relative path")
    return path.as_posix()


class WorkspaceManifestEntry(BaseModel):
    """A content-addressed file contained in a durable workspace snapshot."""

    id: str = Field(min_length=1, max_length=128)
    relative_path: str = Field(min_length=1, max_length=4096)
    object_key: str = Field(min_length=1, max_length=4096)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)
    content_type: str = Field(min_length=1, max_length=255)
    is_executable: bool = False
    created_at: datetime

    @field_validator("relative_path", "object_key")
    @classmethod
    def validate_relative_paths(cls, value: str) -> str:
        return _safe_relative_path(value)


class WorkspaceManifest(BaseModel):
    """Immutable manifest describing the durable contents of one workspace."""

    workspace_id: str = Field(min_length=1, max_length=128)
    tenant_id: str = Field(min_length=1, max_length=128)
    repository_id: str = Field(min_length=1, max_length=128)
    source_revision_id: str = Field(min_length=1, max_length=128)
    purpose: WorkspacePurpose
    storage_uri: str = Field(min_length=5, max_length=4096)
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    entries: list[WorkspaceManifestEntry] = Field(default_factory=list)
    created_at: datetime
    retention_expires_at: datetime

    @field_validator("storage_uri")
    @classmethod
    def validate_storage_uri(cls, value: str) -> str:
        if "://" not in value or "@" in value.split("://", 1)[1].split("/", 1)[0]:
            raise ValueError("storage_uri must be an absolute URI without embedded credentials")
        return value

    @model_validator(mode="after")
    def validate_entries_and_retention(self) -> "WorkspaceManifest":
        paths = [entry.relative_path for entry in self.entries]
        if len(paths) != len(set(paths)):
            raise ValueError("workspace manifest entries must have unique relative paths")
        if self.retention_expires_at <= self.created_at:
            raise ValueError("retention_expires_at must be after created_at")
        return self

    @property
    def total_size_bytes(self) -> int:
        return sum(entry.size_bytes for entry in self.entries)


class WorkspaceRecord(BaseModel):
    """Database-facing workspace metadata without object content."""

    id: str
    tenant_id: str
    repository_id: str
    source_revision_id: str
    parent_workspace_id: str | None = None
    purpose: WorkspacePurpose
    state: WorkspaceState
    storage_uri: str
    manifest_uri: str
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)
    file_count: int = Field(ge=0)
    retention_expires_at: datetime
    created_at: datetime
    ready_at: datetime | None = None
    deleted_at: datetime | None = None
    failure_code: str | None = None
    failure_detail_redacted: str | None = None
