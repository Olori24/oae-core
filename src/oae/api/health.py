from fastapi import APIRouter

from oae.api.config import settings
from oae.api.db import db
from oae.api.postgres_pool import pool_metrics

router = APIRouter(tags=["system"])


@router.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok", "service": "oae-api"}


@router.get("/health/ready")
def ready() -> dict[str, object]:
    with db() as conn:
        conn.execute("SELECT 1").fetchone()
    payload: dict[str, object] = {
        "status": "ok",
        "service": "oae-api",
        "database": settings.database_backend,
    }
    if settings.database_backend == "postgres":
        payload["pool"] = pool_metrics()
    return payload
