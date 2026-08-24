import base64
import json
import time
from collections.abc import Callable, Iterator
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse

from oae.api.auth import (
    TenantPrincipal,
    create_api_key,
    create_principal_api_key,
    require_approver_principal,
    require_owner_principal,
    require_principal,
    require_requester_principal,
    require_tenant,
    revoke_principal_api_key,
)
from oae.api.config import settings
from oae.api.db import db
from oae.api.durable_jobs import DurableJobRepository
from oae.api.job_runner import JobRunner
from oae.api.rate_limits import RateLimitExceeded, rate_limiter
from oae.api.realtime_events import EventCursorExpired, RealtimeEvent, RealtimeEventStore
from oae.api.schemas import (
    JobCreate,
    JobResponse,
    PrincipalKeyCreate,
    PrincipalKeyCreated,
    RepositoryCreate,
    RepositoryResponse,
    RevisionCreate,
    RevisionResponse,
    TenantCreate,
    TenantCreated,
    WorkerAuthorizationCreate,
    WorkerAuthorizationDecision,
    WorkerAuthorizationResponse,
    WorkspaceResponse,
)
from oae.api.worker_authorizations import WorkerAuthorizationError, WorkerAuthorizationRepository

router = APIRouter()
MAX_JOBS_PER_30_DAYS = 1000
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 250


def _sse_response(
    initial_events: list[RealtimeEvent],
    after: int,
    cursor_for: Callable[[RealtimeEvent], int],
    fetch: Callable[[int], list[RealtimeEvent]],
) -> StreamingResponse:
    def stream() -> Iterator[str]:
        cursor = after
        pending = initial_events
        heartbeat_at = time.monotonic()
        closes_at = heartbeat_at + settings.sse_max_connection_seconds
        while time.monotonic() < closes_at:
            events = pending
            pending = []
            if not events:
                events = fetch(cursor)
            for event in events:
                sequence = cursor_for(event)
                if sequence <= cursor:
                    continue
                envelope = json.dumps(event.envelope(), separators=(",", ":"), sort_keys=True)
                yield f"id: {sequence}\nevent: {event.event_type}\ndata: {envelope}\n\n"
                cursor = sequence
            now = time.monotonic()
            if not events and now - heartbeat_at >= settings.sse_heartbeat_seconds:
                yield ": keep-alive\n\n"
                heartbeat_at = now
            if not events:
                time.sleep(max(settings.sse_poll_seconds, 0.1))
        yield "event: stream.closed\ndata: {\"reason\":\"reauthentication_required\"}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


def _cursor_expired_response(exc: EventCursorExpired) -> HTTPException:
    return HTTPException(
        status_code=410,
        detail={"error": "event_cursor_expired", "oldest_sequence": exc.oldest_sequence},
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _decode_cursor(value: str | None) -> tuple[str, str] | None:
    if value is None:
        return None
    try:
        decoded = base64.urlsafe_b64decode(value.encode("ascii") + b"===")
        payload = json.loads(decoded)
        timestamp, item_id = payload["t"], payload["i"]
    except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail="Invalid page cursor") from exc
    if not isinstance(timestamp, str) or not isinstance(item_id, str) or len(timestamp) > 64 or len(item_id) > 160:
        raise HTTPException(status_code=422, detail="Invalid page cursor")
    return timestamp, item_id


def _encode_cursor(timestamp: object, item_id: object) -> str:
    payload = json.dumps({"t": str(timestamp), "i": str(item_id)}, separators=(",", ":"), sort_keys=True)
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")


def _enforce_control_rate(scope: str, subject: str) -> None:
    try:
        rate_limiter.enforce(
            scope=scope,
            subject=subject,
            limit=settings.api_control_rate_limit_per_minute,
        )
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc), headers={"Retry-After": "60"}) from exc


def _repository_response(row) -> RepositoryResponse:
    return RepositoryResponse(
        id=row[0],
        provider=row[1],
        external_id=row[2],
        clone_url=row[3],
        default_branch=row[4],
        status=row[5],
        last_synced_commit=row[6],
        created_at=row[7],
        updated_at=row[8],
    )


def _revision_response(row) -> RevisionResponse:
    return RevisionResponse(
        id=row[0],
        repository_id=row[1],
        commit_sha=row[2],
        tree_sha=row[3],
        branch_name=row[4],
        manifest_sha256=row[5],
        observed_at=row[6],
    )


def _workspace_response(row) -> WorkspaceResponse:
    return WorkspaceResponse(
        id=row[0],
        repository_id=row[1],
        source_revision_id=row[2],
        parent_workspace_id=row[3],
        purpose=row[4],
        state=row[5],
        storage_uri=row[6],
        manifest_uri=row[7],
        manifest_sha256=row[8],
        size_bytes=row[9],
        file_count=row[10],
        retention_expires_at=row[11],
        created_at=row[12],
        ready_at=row[13],
        deleted_at=row[14],
        failure_code=row[15],
    )


@router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    with db() as conn:
        conn.execute("SELECT 1").fetchone()
    return {
        "status": "ok",
        "service": "oae-api",
        "database": settings.database_backend,
    }


@router.post("/v1/tenants", response_model=TenantCreated, status_code=201, tags=["tenants"])
def create_tenant(data: TenantCreate, request: Request) -> TenantCreated:
    _enforce_control_rate("tenant-create", request.client.host if request.client else "unknown")
    tenant_id = str(uuid4())
    with db() as conn:
        conn.execute(
            "INSERT INTO tenants(id,name,created_at) VALUES(?,?,?)",
            (tenant_id, data.name, _now()),
        )
    return TenantCreated(tenant_id=tenant_id, api_key=create_api_key(tenant_id))


@router.get("/v1/me", tags=["tenants"])
def me(tenant_id: str = Depends(require_tenant)) -> dict[str, str]:
    with db() as conn:
        row = conn.execute("SELECT id,name,created_at FROM tenants WHERE id=?", (tenant_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Tenant not found")
    return {"tenant_id": row[0], "name": row[1], "created_at": row[2]}


@router.post("/v1/principal-keys", response_model=PrincipalKeyCreated, status_code=201, tags=["tenants"])
def create_principal_key(
    data: PrincipalKeyCreate,
    principal: TenantPrincipal = Depends(require_principal),
) -> PrincipalKeyCreated:
    principal = require_owner_principal(principal)
    _enforce_control_rate("principal-key-create", principal.tenant_id)
    issued = create_principal_api_key(
        principal.tenant_id,
        principal_id=data.principal_id,
        principal_role=data.principal_role,
    )
    return PrincipalKeyCreated(
        id=issued.id,
        principal_id=issued.principal_id,
        principal_role=issued.principal_role,
        api_key=issued.api_key,
    )


@router.post("/v1/principal-keys/{key_id}/revoke", status_code=204, tags=["tenants"])
def revoke_principal_key(
    key_id: str,
    principal: TenantPrincipal = Depends(require_principal),
) -> None:
    principal = require_owner_principal(principal)
    _enforce_control_rate("principal-key-revoke", principal.tenant_id)
    if key_id == principal.key_id:
        raise HTTPException(status_code=409, detail="An owner cannot revoke the key used for this request.")
    if not revoke_principal_api_key(tenant_id=principal.tenant_id, key_id=key_id):
        raise HTTPException(status_code=404, detail="Principal key not found")


@router.post(
    "/v1/worker-authorizations",
    response_model=WorkerAuthorizationResponse,
    status_code=202,
    tags=["authorizations"],
)
def request_worker_authorization(
    data: WorkerAuthorizationCreate,
    principal: TenantPrincipal = Depends(require_principal),
) -> WorkerAuthorizationResponse:
    principal = require_requester_principal(principal)
    _enforce_control_rate("authorization-request", principal.tenant_id)
    if settings.database_backend != "postgres" or not settings.durable_jobs_enabled:
        raise HTTPException(
            status_code=503,
            detail="Worker authorization requires PostgreSQL with durable jobs enabled.",
        )
    try:
        record = WorkerAuthorizationRepository().request(
            tenant_id=principal.tenant_id,
            operation=data.operation,
            scope=data.scope,
            requester=principal.principal_id,
            expires_in_seconds=data.expires_in_seconds,
        )
    except WorkerAuthorizationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return WorkerAuthorizationResponse(**record.__dict__)


@router.post(
    "/v1/worker-authorizations/{authorization_id}/approve",
    response_model=WorkerAuthorizationResponse,
    tags=["authorizations"],
)
def approve_worker_authorization(
    authorization_id: str,
    data: WorkerAuthorizationDecision,
    principal: TenantPrincipal = Depends(require_principal),
) -> WorkerAuthorizationResponse:
    principal = require_approver_principal(principal)
    _enforce_control_rate("authorization-approve", principal.tenant_id)
    if settings.database_backend != "postgres" or not settings.durable_jobs_enabled:
        raise HTTPException(status_code=503, detail="Worker authorization is unavailable in this runtime.")
    repository = WorkerAuthorizationRepository()
    try:
        repository.approve(
            tenant_id=principal.tenant_id,
            authorization_id=authorization_id,
            approver=principal.principal_id,
            approver_role=principal.role,
            decision_reason_redacted=data.decision_reason_redacted,
        )
    except WorkerAuthorizationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    record = repository.get(tenant_id=principal.tenant_id, authorization_id=authorization_id)
    if not record:
        raise HTTPException(status_code=404, detail="Worker authorization not found")
    return WorkerAuthorizationResponse(**record.__dict__)


@router.post(
    "/v1/worker-authorizations/{authorization_id}/revoke",
    response_model=WorkerAuthorizationResponse,
    tags=["authorizations"],
)
def revoke_worker_authorization(
    authorization_id: str,
    principal: TenantPrincipal = Depends(require_principal),
) -> WorkerAuthorizationResponse:
    principal = require_approver_principal(principal)
    _enforce_control_rate("authorization-revoke", principal.tenant_id)
    if settings.database_backend != "postgres" or not settings.durable_jobs_enabled:
        raise HTTPException(status_code=503, detail="Worker authorization is unavailable in this runtime.")
    repository = WorkerAuthorizationRepository()
    try:
        repository.revoke(
            tenant_id=principal.tenant_id,
            authorization_id=authorization_id,
            approver=principal.principal_id,
            approver_role=principal.role,
        )
    except WorkerAuthorizationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    record = repository.get(tenant_id=principal.tenant_id, authorization_id=authorization_id)
    if not record:
        raise HTTPException(status_code=404, detail="Worker authorization not found")
    return WorkerAuthorizationResponse(**record.__dict__)


@router.get(
    "/v1/worker-authorizations/{authorization_id}",
    response_model=WorkerAuthorizationResponse,
    tags=["authorizations"],
)
def get_worker_authorization(
    authorization_id: str,
    tenant_id: str = Depends(require_tenant),
) -> WorkerAuthorizationResponse:
    if settings.database_backend != "postgres" or not settings.durable_jobs_enabled:
        raise HTTPException(status_code=503, detail="Worker authorization is unavailable in this runtime.")
    record = WorkerAuthorizationRepository().get(tenant_id=tenant_id, authorization_id=authorization_id)
    if not record:
        raise HTTPException(status_code=404, detail="Worker authorization not found")
    return WorkerAuthorizationResponse(**record.__dict__)


@router.post("/v1/repositories", response_model=RepositoryResponse, status_code=201, tags=["repositories"])
def create_repository(
    data: RepositoryCreate,
    tenant_id: str = Depends(require_tenant),
) -> RepositoryResponse:
    repository_id = str(uuid4())
    now = _now()
    with db() as conn:
        inserted = conn.execute(
            """
            INSERT INTO repositories(
                id,tenant_id,provider,external_id,clone_url,default_branch,credential_ref,
                status,last_synced_commit,created_at,updated_at,deleted_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(tenant_id,provider,external_id) DO NOTHING
            """,
            (
                repository_id,
                tenant_id,
                data.provider,
                data.external_id,
                data.clone_url,
                data.default_branch,
                data.credential_ref,
                "active",
                None,
                now,
                now,
                None,
            ),
        )
        if inserted.rowcount == 0:
            raise HTTPException(status_code=409, detail="Repository is already registered for this tenant")
    return RepositoryResponse(
        id=repository_id,
        provider=data.provider,
        external_id=data.external_id,
        clone_url=data.clone_url,
        default_branch=data.default_branch,
        status="active",
        last_synced_commit=None,
        created_at=_timestamp(now),
        updated_at=_timestamp(now),
    )


@router.get("/v1/repositories", response_model=list[RepositoryResponse], tags=["repositories"])
def list_repositories(
    response: Response,
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    after: str | None = Query(default=None, max_length=512),
    tenant_id: str = Depends(require_tenant),
) -> list[RepositoryResponse]:
    cursor = _decode_cursor(after)
    query = """
        SELECT id,provider,external_id,clone_url,default_branch,status,last_synced_commit,created_at,updated_at
        FROM repositories
        WHERE tenant_id=? AND deleted_at IS NULL
    """
    params: list[object] = [tenant_id]
    if cursor:
        query += " AND (updated_at < ? OR (updated_at = ? AND id < ?))"
        params.extend((cursor[0], cursor[0], cursor[1]))
    query += " ORDER BY updated_at DESC, id DESC LIMIT ?"
    params.append(limit + 1)
    with db() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
    page = rows[:limit]
    if len(rows) > limit and page:
        response.headers["X-Next-Cursor"] = _encode_cursor(page[-1][8], page[-1][0])
    return [_repository_response(row) for row in page]


@router.post(
    "/v1/repositories/{repository_id}/revisions",
    response_model=RevisionResponse,
    status_code=201,
    tags=["repositories"],
)
def pin_repository_revision(
    repository_id: str,
    data: RevisionCreate,
    tenant_id: str = Depends(require_tenant),
) -> RevisionResponse:
    revision_id = str(uuid4())
    observed_at = _now()
    with db() as conn:
        repository = conn.execute(
            """
            SELECT id FROM repositories
            WHERE id=? AND tenant_id=? AND status='active' AND deleted_at IS NULL
            """,
            (repository_id, tenant_id),
        ).fetchone()
        if not repository:
            raise HTTPException(status_code=404, detail="Repository not found")
        inserted = conn.execute(
            """
            INSERT INTO repository_revisions(
                id,tenant_id,repository_id,commit_sha,tree_sha,branch_name,manifest_sha256,observed_at
            ) VALUES(?,?,?,?,?,?,?,?)
            ON CONFLICT(tenant_id,repository_id,commit_sha) DO NOTHING
            """,
            (
                revision_id,
                tenant_id,
                repository_id,
                data.commit_sha,
                data.tree_sha,
                data.branch_name,
                data.manifest_sha256,
                observed_at,
            ),
        )
        if inserted.rowcount == 0:
            raise HTTPException(status_code=409, detail="Revision is already pinned for this repository")
        conn.execute(
            "UPDATE repositories SET last_synced_commit=?, updated_at=? WHERE id=? AND tenant_id=?",
            (data.commit_sha, observed_at, repository_id, tenant_id),
        )
    return RevisionResponse(
        id=revision_id,
        repository_id=repository_id,
        commit_sha=data.commit_sha,
        tree_sha=data.tree_sha,
        branch_name=data.branch_name,
        manifest_sha256=data.manifest_sha256,
        observed_at=_timestamp(observed_at),
    )


@router.get(
    "/v1/repositories/{repository_id}/revisions",
    response_model=list[RevisionResponse],
    tags=["repositories"],
)
def list_repository_revisions(
    repository_id: str,
    response: Response,
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    after: str | None = Query(default=None, max_length=512),
    tenant_id: str = Depends(require_tenant),
) -> list[RevisionResponse]:
    cursor = _decode_cursor(after)
    with db() as conn:
        repository = conn.execute(
            "SELECT id FROM repositories WHERE id=? AND tenant_id=? AND deleted_at IS NULL",
            (repository_id, tenant_id),
        ).fetchone()
        if not repository:
            raise HTTPException(status_code=404, detail="Repository not found")
        query = """
            SELECT id,repository_id,commit_sha,tree_sha,branch_name,manifest_sha256,observed_at
            FROM repository_revisions WHERE tenant_id=? AND repository_id=?
        """
        params: list[object] = [tenant_id, repository_id]
        if cursor:
            query += " AND (observed_at < ? OR (observed_at = ? AND id < ?))"
            params.extend((cursor[0], cursor[0], cursor[1]))
        query += " ORDER BY observed_at DESC, id DESC LIMIT ?"
        params.append(limit + 1)
        rows = conn.execute(query, tuple(params)).fetchall()
    page = rows[:limit]
    if len(rows) > limit and page:
        response.headers["X-Next-Cursor"] = _encode_cursor(page[-1][6], page[-1][0])
    return [_revision_response(row) for row in page]


@router.get("/v1/workspaces", response_model=list[WorkspaceResponse], tags=["workspaces"])
def list_workspaces(
    response: Response,
    repository_id: str | None = Query(default=None, min_length=1, max_length=120),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    after: str | None = Query(default=None, max_length=512),
    tenant_id: str = Depends(require_tenant),
) -> list[WorkspaceResponse]:
    cursor = _decode_cursor(after)
    query = """
        SELECT id,repository_id,source_revision_id,parent_workspace_id,purpose,state,storage_uri,manifest_uri,
               manifest_sha256,size_bytes,file_count,retention_expires_at,created_at,ready_at,deleted_at,failure_code
        FROM workspaces
        WHERE tenant_id=?
    """
    params: list[object] = [tenant_id]
    if repository_id is not None:
        query += " AND repository_id=?"
        params.append(repository_id)
    if cursor:
        query += " AND (created_at < ? OR (created_at = ? AND id < ?))"
        params.extend((cursor[0], cursor[0], cursor[1]))
    query += " ORDER BY created_at DESC, id DESC LIMIT ?"
    params.append(limit + 1)
    with db() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
    page = rows[:limit]
    if len(rows) > limit and page:
        response.headers["X-Next-Cursor"] = _encode_cursor(page[-1][12], page[-1][0])
    return [_workspace_response(row) for row in page]


@router.get("/v1/workspaces/{workspace_id}", response_model=WorkspaceResponse, tags=["workspaces"])
def get_workspace(workspace_id: str, tenant_id: str = Depends(require_tenant)) -> WorkspaceResponse:
    with db() as conn:
        row = conn.execute(
            """
            SELECT id,repository_id,source_revision_id,parent_workspace_id,purpose,state,storage_uri,manifest_uri,
                   manifest_sha256,size_bytes,file_count,retention_expires_at,created_at,ready_at,deleted_at,failure_code
            FROM workspaces
            WHERE id=? AND tenant_id=?
            """,
            (workspace_id, tenant_id),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return _workspace_response(row)


@router.post("/v1/jobs", response_model=JobResponse, status_code=202, tags=["jobs"])
def create_job(
    data: JobCreate,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(require_tenant),
) -> JobResponse:
    _enforce_control_rate("job-create", tenant_id)
    if data.operation == "build" and settings.worker_authorization_enforcement_enabled:
        if settings.database_backend != "postgres" or not settings.durable_jobs_enabled:
            raise HTTPException(
                status_code=503,
                detail="Build execution requires PostgreSQL durable jobs while authorization enforcement is enabled.",
            )
        if not WorkerAuthorizationRepository().is_approved_for_execution(
            tenant_id=tenant_id,
            authorization_id=data.authorization_id,
            operation=data.operation,
        ):
            raise HTTPException(
                status_code=403,
                detail="Build execution requires an active tenant-scoped worker authorization.",
            )
    if settings.durable_jobs_enabled:
        durable_job = DurableJobRepository().enqueue(
            tenant_id=tenant_id,
            operation=data.operation,
            payload=data.payload,
            idempotency_key=data.idempotency_key,
            workspace_id=data.workspace_id,
            authorization_id=data.authorization_id,
            priority=data.priority,
        )
        return JobResponse(
            id=durable_job.id,
            status=durable_job.status,
            operation=durable_job.operation,
            payload=durable_job.payload,
            created_at=durable_job.created_at,
            updated_at=durable_job.updated_at,
        )
    job_id = str(uuid4())
    now = _now()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    with db() as conn:
        recent = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE tenant_id=? AND created_at >= ?",
            (tenant_id, cutoff),
        ).fetchone()[0]
        if recent >= MAX_JOBS_PER_30_DAYS:
            raise HTTPException(status_code=429, detail="Monthly job quota exceeded")
        conn.execute(
            "INSERT INTO jobs(id,tenant_id,status,operation,payload,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
            (job_id, tenant_id, "queued", data.operation, json.dumps(data.payload), now, now),
        )
    background_tasks.add_task(JobRunner().run, job_id)
    return JobResponse(
        id=job_id,
        status="queued",
        operation=data.operation,
        payload=data.payload,
        created_at=_timestamp(now),
        updated_at=_timestamp(now),
    )


@router.get("/v1/jobs", response_model=list[JobResponse], tags=["jobs"])
def list_jobs(
    response: Response,
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    after: str | None = Query(default=None, max_length=512),
    tenant_id: str = Depends(require_tenant),
) -> list[JobResponse]:
    cursor = _decode_cursor(after)
    query = "SELECT id,status,operation,payload,result,created_at,updated_at FROM jobs WHERE tenant_id=?"
    params: list[object] = [tenant_id]
    if cursor:
        query += " AND (created_at < ? OR (created_at = ? AND id < ?))"
        params.extend((cursor[0], cursor[0], cursor[1]))
    query += " ORDER BY created_at DESC, id DESC LIMIT ?"
    params.append(limit + 1)
    with db() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
    page = rows[:limit]
    if len(rows) > limit and page:
        response.headers["X-Next-Cursor"] = _encode_cursor(page[-1][5], page[-1][0])
    return [
        JobResponse(
            id=r[0], status=r[1], operation=r[2], payload=json.loads(r[3]),
            result=json.loads(r[4]) if r[4] else None, created_at=r[5], updated_at=r[6]
        ) for r in page
    ]


@router.get("/v1/jobs/{job_id}", response_model=JobResponse, tags=["jobs"])
def get_job(job_id: str, tenant_id: str = Depends(require_tenant)) -> JobResponse:
    with db() as conn:
        row = conn.execute(
            "SELECT id,status,operation,payload,result,created_at,updated_at FROM jobs WHERE id=? AND tenant_id=?",
            (job_id, tenant_id),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(
        id=row[0], status=row[1], operation=row[2], payload=json.loads(row[3]),
        result=json.loads(row[4]) if row[4] else None, created_at=row[5], updated_at=row[6]
    )


@router.get("/v1/events/snapshot", tags=["events"])
def event_snapshot(tenant_id: str = Depends(require_tenant)) -> dict:
    return RealtimeEventStore().snapshot(tenant_id)


@router.get("/v1/events", tags=["events"])
def stream_tenant_events(
    after: int = Query(default=0, ge=0),
    tenant_id: str = Depends(require_tenant),
) -> StreamingResponse:
    store = RealtimeEventStore()
    try:
        initial = store.list_tenant_events(tenant_id, after)
    except EventCursorExpired as exc:
        raise _cursor_expired_response(exc) from exc
    return _sse_response(
        initial,
        after,
        lambda event: event.tenant_sequence,
        lambda cursor: store.list_tenant_events(tenant_id, cursor),
    )


def _stream_aggregate_events(
    tenant_id: str,
    aggregate_type: str,
    aggregate_id: str,
    after: int,
) -> StreamingResponse:
    store = RealtimeEventStore()
    if not store.assert_aggregate_owned(tenant_id, aggregate_type, aggregate_id):
        raise HTTPException(status_code=404, detail=f"{aggregate_type.title()} not found")
    try:
        initial = store.list_aggregate_events(tenant_id, aggregate_type, aggregate_id, after)
    except EventCursorExpired as exc:
        raise _cursor_expired_response(exc) from exc
    return _sse_response(
        initial,
        after,
        lambda event: event.aggregate_sequence,
        lambda cursor: store.list_aggregate_events(tenant_id, aggregate_type, aggregate_id, cursor),
    )


@router.get("/v1/jobs/{job_id}/events", tags=["events"])
def stream_job_events(
    job_id: str,
    after: int = Query(default=0, ge=0),
    tenant_id: str = Depends(require_tenant),
) -> StreamingResponse:
    return _stream_aggregate_events(tenant_id, "job", job_id, after)


@router.get("/v1/workspaces/{workspace_id}/events", tags=["events"])
def stream_workspace_events(
    workspace_id: str,
    after: int = Query(default=0, ge=0),
    tenant_id: str = Depends(require_tenant),
) -> StreamingResponse:
    return _stream_aggregate_events(tenant_id, "workspace", workspace_id, after)
    PrincipalKeyCreate,
    PrincipalKeyCreated,
