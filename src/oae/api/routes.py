import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from oae.api.auth import create_api_key, require_tenant
from oae.api.config import settings
from oae.api.db import db
from oae.api.job_runner import JobRunner
from oae.api.schemas import JobCreate, JobResponse, TenantCreate, TenantCreated

router = APIRouter()
MAX_JOBS_PER_30_DAYS = 1000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


@router.post("/v1/jobs", response_model=JobResponse, status_code=202, tags=["jobs"])
def create_job(
    data: JobCreate,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(require_tenant),
) -> JobResponse:
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
    return JobResponse(id=job_id, status="queued", operation=data.operation, payload=data.payload, created_at=now, updated_at=now)


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
