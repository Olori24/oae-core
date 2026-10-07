"""Authenticated durable worker tick endpoint for serverless deployment."""
from __future__ import annotations

import os
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException

from oae.api.durable_jobs import DurableJobRepository
from oae.api.job_runner import JobRunner

router = APIRouter(prefix="/v1/worker", tags=["worker"])


def _authorized(authorization: str | None, cron_secret: str | None) -> bool:
    if not cron_secret or not authorization:
        return False
    return authorization == f"Bearer {cron_secret}"


@router.post("/tick")
def worker_tick(authorization: str | None = Header(default=None)) -> dict:
    cron_secret = os.getenv("CRON_SECRET")
    if not _authorized(authorization, cron_secret):
        raise HTTPException(status_code=401, detail="Worker authentication failed.")

    repository = DurableJobRepository()
    worker_name = f"vercel-cron-{uuid4().hex[:12]}"
    worker_id = repository.register_worker(
        worker_name=worker_name,
        pool="engineering",
        capabilities={"serverless": True, "governed_execution": True},
    )
    processed = 0
    failed = 0
    for _ in range(3):
        lease = repository.claim_next(worker_id)
        if lease is None:
            break
        JobRunner().run_lease(lease)
        processed += 1
    return {"status": "ok", "worker_id": worker_id, "processed": processed, "failed": failed}
