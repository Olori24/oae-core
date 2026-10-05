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
from oae.api.agent_runs import AgentRunRepository
from pydantic import BaseModel, ConfigDict, Field


router = APIRouter(prefix="/v1/engineering", tags=["engineering"])


class EngineeringRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)



class EngineeringPlanRequest(EngineeringRequest):
    workspace_id: str = Field(min_length=1, max_length=120)
    authorization_id: str = Field(min_length=1, max_length=120)
    objective: str = Field(min_length=1, max_length=4000)
    repository_kind: Literal["python", "node", "typescript", "mixed", "unknown"] = "unknown"
    has_tests: bool = True
    has_linter: bool = True
    has_typecheck: bool = False
    has_build: bool = False
    test_runner: Literal["none", "vitest", "jest"] = "none"
    security_required: bool = True
    action_inputs: dict[str, dict] = Field(default_factory=dict, max_length=32)


class AgentDecisionRequest(EngineeringRequest):
    authorization_id: str = Field(min_length=1, max_length=120)
    plan: dict
    completed_steps: list[str] = Field(default_factory=list, max_length=32)

class AgentRunStartRequest(EngineeringRequest):
    workspace_id: str = Field(min_length=1, max_length=120)
    authorization_id: str = Field(min_length=1, max_length=120)
    plan: dict
    max_repairs: int = Field(default=2, ge=0, le=3)
    run_idempotency_key: str | None = Field(default=None, min_length=1, max_length=200)
    correlation_id: str | None = Field(default=None, min_length=1, max_length=200)


class AgentRunStepRequest(EngineeringRequest):
    run_id: str = Field(min_length=1, max_length=120)
    authorization_id: str = Field(min_length=1, max_length=120)
    step_id: str = Field(min_length=1, max_length=120)
    success: bool
    evidence: dict | None = None



class CiStatusRequest(EngineeringRequest):
    workspace_id: str = Field(min_length=1, max_length=120)
    authorization_id: str = Field(min_length=1, max_length=120)
    commit_sha: str = Field(min_length=40, max_length=40)


class ProductionReadinessRequest(EngineeringRequest):
    workspace_id: str = Field(min_length=1, max_length=120)
    authorization_id: str = Field(min_length=1, max_length=120)
    quality_verified: bool
    workspace_verified: bool
    ci_status: Literal["passed", "pending", "failed"]
    change_set_synced: bool
    pull_request_open: bool
    deployment_verified: bool = False
    rollback_verified: bool = False

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

class ChangeSetSyncRequest(EngineeringRequest):
    workspace_id: str = Field(min_length=1, max_length=120)
    authorization_id: str = Field(min_length=1, max_length=120)
    branch: str = Field(min_length=1, max_length=120)
    message: str | None = Field(default=None, max_length=200)
    title: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=2000)


class PullRequestRequest(EngineeringRequest):
    change_set_id: str = Field(min_length=1, max_length=120)
    authorization_id: str = Field(min_length=1, max_length=120)

class CommandExecutionRequest(EngineeringRequest):
    workspace_id: str = Field(min_length=1, max_length=120)
    authorization_id: str = Field(min_length=1, max_length=120)
    command: Literal["python_compile", "pytest", "ruff", "mypy", "typescript_check", "eslint_check", "vitest_check", "jest_check"]


class WorkspaceVerificationRequest(EngineeringRequest):
    workspace_id: str = Field(min_length=1, max_length=120)
    authorization_id: str = Field(min_length=1, max_length=120)
    commands: list[Literal["python_compile", "pytest", "ruff", "mypy", "typescript_check"]] = Field(default_factory=lambda: ["python_compile", "ruff", "pytest"], max_length=8)


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



@router.post("/plans/create", response_model=JobResponse, status_code=202)
def create_engineering_plan(
    data: EngineeringPlanRequest,
    principal: TenantPrincipal = Depends(require_principal),
) -> JobResponse:
    return _queue(
        principal=principal,
        authorization_id=data.authorization_id,
        stage="plan",
        payload=data.model_dump(exclude={"authorization_id"}),
    )


@router.post("/agent/next", response_model=JobResponse, status_code=202)
def select_next_agent_action(
    data: AgentDecisionRequest,
    principal: TenantPrincipal = Depends(require_principal),
) -> JobResponse:
    return _queue(
        principal=principal,
        authorization_id=data.authorization_id,
        stage="agent",
        payload=data.model_dump(exclude={"authorization_id"}),
    )



@router.post("/agent/runs/start", response_model=JobResponse, status_code=202)
def start_agent_run(
    data: AgentRunStartRequest,
    principal: TenantPrincipal = Depends(require_principal),
) -> JobResponse:
    return _queue(
        principal=principal,
        authorization_id=data.authorization_id,
        stage="agent_run_start",
        payload=data.model_dump(exclude={"authorization_id"}, exclude_none=True),
    )


@router.post("/agent/runs/step", response_model=JobResponse, status_code=202)
def record_agent_run_step(
    data: AgentRunStepRequest,
    principal: TenantPrincipal = Depends(require_principal),
) -> JobResponse:
    return _queue(
        principal=principal,
        authorization_id=data.authorization_id,
        stage="agent_run_step",
        payload=data.model_dump(exclude={"authorization_id"}, exclude_none=True),
    )


@router.get("/agent/runs/{run_id}")
def get_agent_run(
    run_id: str,
    principal: TenantPrincipal = Depends(require_principal),
) -> dict:
    principal = require_requester_principal(principal)
    record = AgentRunRepository().get(tenant_id=principal.tenant_id, run_id=run_id)
    decision = record.state.next_decision() if record.state.status == "running" else None
    return {
        "id": record.id,
        "workspace_id": record.workspace_id,
        "status": record.state.status,
        "completed_steps": list(record.state.completed_steps),
        "failed_step": record.state.failed_step,
        "repair_count": record.state.repair_count,
        "decision": decision.to_dict() if decision else None,
        "evidence": list(record.state.evidence),
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


@router.post("/ci/status", response_model=JobResponse, status_code=202)
def inspect_ci_status(
    data: CiStatusRequest,
    principal: TenantPrincipal = Depends(require_principal),
) -> JobResponse:
    return _queue(
        principal=principal,
        authorization_id=data.authorization_id,
        stage="ci_status",
        payload=data.model_dump(exclude={"authorization_id"}),
    )


@router.post("/readiness/gate", response_model=JobResponse, status_code=202)
def evaluate_readiness_gate(
    data: ProductionReadinessRequest,
    principal: TenantPrincipal = Depends(require_principal),
) -> JobResponse:
    return _queue(
        principal=principal,
        authorization_id=data.authorization_id,
        stage="readiness_gate",
        payload=data.model_dump(exclude={"authorization_id"}),
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



@router.post("/changesets/sync", response_model=JobResponse, status_code=202)
def synchronize_change_set(
    data: ChangeSetSyncRequest,
    principal: TenantPrincipal = Depends(require_principal),
) -> JobResponse:
    return _queue(
        principal=principal,
        authorization_id=data.authorization_id,
        stage="sync",
        payload=data.model_dump(exclude={"authorization_id"}, exclude_none=True),
    )


@router.post("/changesets/pull-request", response_model=JobResponse, status_code=202)
def create_change_set_pull_request(
    data: PullRequestRequest,
    principal: TenantPrincipal = Depends(require_principal),
) -> JobResponse:
    return _queue(
        principal=principal,
        authorization_id=data.authorization_id,
        stage="pull_request",
        payload=data.model_dump(exclude={"authorization_id"}, exclude_none=True),
    )


@router.post("/workspaces/execute", response_model=JobResponse, status_code=202)
def execute_governed_command(
    data: CommandExecutionRequest,
    principal: TenantPrincipal = Depends(require_principal),
) -> JobResponse:
    return _queue(
        principal=principal,
        authorization_id=data.authorization_id,
        stage="execute",
        payload=data.model_dump(exclude={"authorization_id"}, exclude_none=True),
    )


@router.post("/workspaces/verify", response_model=JobResponse, status_code=202)
def verify_workspace_commands(
    data: WorkspaceVerificationRequest,
    principal: TenantPrincipal = Depends(require_principal),
) -> JobResponse:
    return _queue(
        principal=principal,
        authorization_id=data.authorization_id,
        stage="verify",
        payload=data.model_dump(exclude={"authorization_id"}, exclude_none=True),
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
