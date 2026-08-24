from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_GITHUB_REPOSITORY_ID_PATTERN = r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$"
_GIT_SHA_PATTERN = r"^[a-fA-F0-9]{40}$"
_SHA256_PATTERN = r"^[a-fA-F0-9]{64}$"
_BRANCH_NAME_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TenantCreate(_StrictModel):
    name: str = Field(min_length=2, max_length=120)


class TenantCreated(_StrictModel):
    tenant_id: str
    api_key: str


class PrincipalKeyCreate(_StrictModel):
    principal_role: Literal["operator", "approver", "viewer"]
    principal_id: str | None = Field(default=None, min_length=2, max_length=120)


class PrincipalKeyCreated(_StrictModel):
    id: str
    principal_id: str
    principal_role: str = Field(pattern=r"^(operator|approver|viewer)$")
    api_key: str


class JobCreate(_StrictModel):
    operation: str = Field(pattern=r"^(analyze|review|verify|build)$")
    payload: dict = Field(default_factory=dict)
    workspace_id: str | None = Field(default=None, min_length=1, max_length=120)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=200)
    priority: int = Field(default=100, ge=0, le=1000)
    authorization_id: str | None = Field(default=None, min_length=1, max_length=120)


class JobResponse(_StrictModel):
    id: str
    status: str
    operation: str
    payload: dict
    result: dict | None = None
    created_at: datetime
    updated_at: datetime


class WorkerAuthorizationCreate(_StrictModel):
    operation: Literal["build"]
    scope: dict[str, str] = Field(default_factory=dict, max_length=20)
    expires_in_seconds: int = Field(default=3600, ge=60, le=7 * 24 * 60 * 60)


class WorkerAuthorizationDecision(_StrictModel):
    decision_reason_redacted: str | None = Field(default=None, min_length=1, max_length=500)


class WorkerAuthorizationResponse(_StrictModel):
    id: str
    operation: Literal["build"]
    scope: dict[str, str]
    requester: str
    status: Literal["pending", "approved", "rejected", "revoked", "expired"]
    requested_at: datetime
    expires_at: datetime
    decided_at: datetime | None = None
    decided_by: str | None = None
    decided_role: str | None = None
    decision_reason_redacted: str | None = None
    revoked_at: datetime | None = None
    revoked_by: str | None = None
    revoked_role: str | None = None


class RepositoryCreate(_StrictModel):
    provider: Literal["github"] = "github"
    external_id: str = Field(pattern=_GITHUB_REPOSITORY_ID_PATTERN, max_length=200)
    clone_url: str = Field(min_length=20, max_length=500)
    default_branch: str = Field(default="main", pattern=_BRANCH_NAME_PATTERN, max_length=255)
    credential_ref: str | None = Field(default=None, min_length=1, max_length=500)

    @field_validator("clone_url")
    @classmethod
    def validate_clone_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "github.com"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("clone_url must be a credential-free HTTPS GitHub clone URL")
        return value

    @model_validator(mode="after")
    def clone_url_must_match_repository(self) -> "RepositoryCreate":
        if urlparse(self.clone_url).path != f"/{self.external_id}.git":
            raise ValueError("clone_url must match external_id and end in .git")
        return self

    @field_validator("credential_ref")
    @classmethod
    def validate_credential_ref(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed = urlparse(value)
        if (
            parsed.scheme
            not in {"secret", "vault", "aws-secretsmanager", "gcp-secret-manager"}
            or (not parsed.netloc and not parsed.path)
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("credential_ref must be an external secret-manager reference")
        return value


class RepositoryResponse(_StrictModel):
    id: str
    provider: Literal["github"]
    external_id: str
    clone_url: str
    default_branch: str
    status: Literal["active", "revoked", "error"]
    last_synced_commit: str | None = None
    created_at: datetime
    updated_at: datetime


class RevisionCreate(_StrictModel):
    commit_sha: str = Field(pattern=_GIT_SHA_PATTERN)
    tree_sha: str | None = Field(default=None, pattern=_GIT_SHA_PATTERN)
    branch_name: str | None = Field(default=None, pattern=_BRANCH_NAME_PATTERN, max_length=255)
    manifest_sha256: str | None = Field(default=None, pattern=_SHA256_PATTERN)

    @field_validator("commit_sha", "tree_sha", "manifest_sha256")
    @classmethod
    def normalize_sha(cls, value: str | None) -> str | None:
        return value.lower() if value is not None else None


class RevisionResponse(_StrictModel):
    id: str
    repository_id: str
    commit_sha: str
    tree_sha: str | None = None
    branch_name: str | None = None
    manifest_sha256: str | None = None
    observed_at: datetime


class WorkspaceResponse(_StrictModel):
    id: str
    repository_id: str
    source_revision_id: str
    parent_workspace_id: str | None = None
    purpose: Literal["source", "execution", "output", "review"]
    state: Literal["provisioning", "ready", "deleting", "deleted", "failed"]
    storage_uri: str
    manifest_uri: str
    manifest_sha256: str
    size_bytes: int = Field(ge=0)
    file_count: int = Field(ge=0)
    retention_expires_at: datetime
    created_at: datetime
    ready_at: datetime | None = None
    deleted_at: datetime | None = None
    failure_code: str | None = None
