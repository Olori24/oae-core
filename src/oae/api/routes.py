import json
import time
from collections.abc import Callable, Iterator
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from oae.api.auth import create_api_key, require_tenant
from oae.api.config import settings
from oae.api.db import db
from oae.api.durable_jobs import DurableJobRepository
from oae.api.job_runner import JobRunner
from oae.api.realtime_events import EventCursorExpired, RealtimeEvent, RealtimeEventStore
from oae.api.schemas import (
    JobCreate,
    JobResponse,
    RepositoryCreate,
    RepositoryResponse,
    RevisionCreate,
    RevisionResponse,
    TenantCreate,
    TenantCreated,
)

router = APIRouter()
MAX_JOBS_PER_30_DAYS = 1000


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
def create_tenant(data: TenantCreate) -> TenantCreated:
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


@router.post("/v1/jobs", response_model=JobResponse, status_code=202, tags=["jobs"])
def create_job(
    data: JobCreate,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(require_tenant),
) -> JobResponse:
    if settings.durable_jobs_enabled:
        durable_job = DurableJobRepository().enqueue(
            tenant_id=tenant_id,
            operation=data.operation,
            payload=data.payload,
            idempotency_key=data.idempotency_key,
            workspace_id=data.workspace_id,
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
def list_jobs(tenant_id: str = Depends(require_tenant)) -> list[JobResponse]:
    with db() as conn:
        rows = conn.execute(
            "SELECT id,status,operation,payload,result,created_at,updated_at FROM jobs WHERE tenant_id=? ORDER BY created_at DESC LIMIT 100",
            (tenant_id,),
        ).fetchall()
    return [
        JobResponse(
            id=r[0], status=r[1], operation=r[2], payload=json.loads(r[3]),
            result=json.loads(r[4]) if r[4] else None, created_at=r[5], updated_at=r[6]
        ) for r in rows
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
