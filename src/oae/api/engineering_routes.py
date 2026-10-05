"""High-level engineering pipeline routes.

These routes make the first repository-to-readiness workflow explicit while
keeping consequential execution behind the existing worker-authorization gate.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException

from oae.api.auth import TenantPrincipal, require_principal, require_requester_principal
from oae.api.config import settings
from oae.api.durable_jobs import DurableJobRepository
from oae.api.rate_limits import RateLimitExceeded, rate_limiter
from oae.api.schemas import JobResponse
from oae.api.worker_authorizations import WorkerAuthorizationRepository
from pydantic import BaseModel, ConfigDict, Field


router = APIRouter(prefix="/v1/engineering", tags=["engineering"])


class EngineeringRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class WorkspaceProvisionRequest(EngineeringRequest):
    repository_id: str = Field(min_length=1, max_length=120)
    revision_id: str = Field(min_length=1, max_length=120)
    purpose: Literal["source", "execution", "output", "review"] = "source"
    parent_workspace_id: str | None = Field(default=None, min_length=1, max_length=120)
    authorization_id: str = Field(min_length=1, max_length=120)


class WorkspaceValidationRequest(EngineeringRequest):
    workspace_id: str = Field(min_length=1, max_length=120)
    authorization_id: str = Field(min_length=1, max_length=120)

class WorktreeRequest(EngineeringRequest):
    workspace_id: str = Field(min_length=1, max_length=120)
    authorization_id: str = Field(min_length=1, max_length=120)
    branch: str | None = Field(default=None, max_length=120)
    path: str | None = Field(default=None, max_length=4096)
    content: str | None = None
    message: str | None = Field(default=None, max_length=200)


def _queue(
    *,
    principal: TenantPrincipal,
    payload: dict,
    authorization_id: str,
    stage: str,
) -> JobResponse:
    principal = require_requester_principal(principal)
    tenant_id = principal.tenant_id
    try:
        rate_limiter.enforce(
            scope=f"engineering-{stage}",
            subject=tenant_id,
            limit=settings.api_control_rate_limit_per_minute,
        )
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc), headers={"Retry-After": "60"}) from exc

    if not settings.durable_jobs_enabled or settings.database_backend != "postgres":
        raise HTTPException(
            status_code=503,
            detail="Engineering execution requires PostgreSQL durable jobs.",
        )
    if not WorkerAuthorizationRepository().is_approved_for_execution(
        tenant_id=tenant_id,
        authorization_id=authorization_id,
        operation="build",
    ):
        raise HTTPException(
            status_code=403,
            detail="Engineering execution requires an active tenant-scoped worker authorization.",
        )

    job = DurableJobRepository().enqueue(
        tenant_id=tenant_id,
        operation="build",
        payload={**payload, "stage": stage},
        authorization_id=authorization_id,
        idempotency_key=payload.get("idempotency_key"),
        priority=payload.get("priority", 100),
    )
    return JobResponse(
        id=job.id,
        status=job.status,
        operation=job.operation,
        payload=job.payload,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.post("/workspaces/provision", response_model=JobResponse, status_code=202)
def provision_workspace(
    data: WorkspaceProvisionRequest,
    principal: TenantPrincipal = Depends(require_principal),
) -> JobResponse:
    return _queue(
        principal=principal,
        authorization_id=data.authorization_id,
        stage="provision",
        payload=data.model_dump(exclude={"authorization_id"}),
    )


@router.post("/workspaces/validate", response_model=JobResponse, status_code=202)
def validate_workspace(
    data: WorkspaceValidationRequest,
    principal: TenantPrincipal = Depends(require_principal),
) -> JobResponse:
    return _queue(
        principal=principal,
        authorization_id=data.authorization_id,
        stage="validate",
        payload=data.model_dump(exclude={"authorization_id"}),
    )


@router.post("/workspaces/readiness", response_model=JobResponse, status_code=202)
def check_workspace_readiness(
    data: WorkspaceValidationRequest,
    principal: TenantPrincipal = Depends(require_principal),
) -> JobResponse:
    return _queue(
        principal=principal,
        authorization_id=data.authorization_id,
        stage="readiness",
        payload=data.model_dump(exclude={"authorization_id"}),
    )


@router.post("/workspaces/{stage}", response_model=JobResponse, status_code=202)
def worktree_operation(
    stage: Literal["attach", "branch", "write", "delete", "diff", "commit"],
    data: WorktreeRequest,
    principal: TenantPrincipal = Depends(require_principal),
) -> JobResponse:
    required = {
        "branch": data.branch,
        "write": data.path,
        "delete": data.path,
        "commit": data.message,
    }.get(stage)
    if stage in {"branch", "write", "delete", "commit"} and not required:
        raise HTTPException(status_code=422, detail=f"{stage} requires its corresponding payload field.")
    return _queue(
        principal=principal,
        authorization_id=data.authorization_id,
        stage=stage,
        payload=data.model_dump(exclude={"authorization_id"}, exclude_none=True),
    )
