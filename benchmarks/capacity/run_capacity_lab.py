#!/usr/bin/env python3
"""Integrated OAE capacity lab: baseline, concurrency, tenant isolation, durable recovery."""
from __future__ import annotations
import asyncio, json, os, platform, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "benchmarks" / "capacity"
RESULTS = OUT / "results.json"
REPORT = OUT / "CAPACITY_REPORT.md"

def percentile(values: list[float], p: float) -> float | None:
    if not values: return None
    values = sorted(values)
    if len(values) == 1: return values[0]
    rank = (len(values) - 1) * p / 100
    lo, hi = int(rank), min(int(rank) + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (rank - lo)

def env_levels() -> list[int]:
    raw = os.getenv("OAE_CAPACITY_LEVELS", "10,25,50,100,250,500,1000")
    return sorted(set(int(x.strip()) for x in raw.split(",") if x.strip() and int(x.strip()) > 0))

def process_resources() -> dict[str, Any]:
    try:
        import resource
        return {"max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    except Exception:
        return {"max_rss_kb": None}

def make_report(result: dict[str, Any]) -> None:
    lines = [
        "# OAE Core Capacity Report", "",
        "Revision: " + str(result["revision"]),
        "Started: " + str(result["started_at"]),
        "Finished: " + str(result["finished_at"]),
        "Python: " + str(result["runtime"]["python"]),
        "Platform: " + str(result["runtime"]["platform"]),
        "Database backend: " + str(result["runtime"]["database_backend"]), "",
        "## Acceptance gates", "",
        "- Security/isolation violation: " + ("FAIL" if result["gates"]["isolation_violation"] else "PASS"),
        "- Silent job loss: " + ("FAIL" if result["gates"]["silent_job_loss"] else "PASS"),
        "- Unbounded stuck jobs: " + ("FAIL" if result["gates"]["stuck_jobs"] else "PASS"), "",
        "## Phase 1 — Baseline", "",
    ]
    for item in result["baseline"]:
        lines.append("- " + str(item["operation"]) + ": HTTP " + str(item.get("status_code", "n/a")) + ", " + f'{item.get("latency_ms", 0):.2f}' + " ms")
    lines += ["", "## Phase 2 — Concurrency", "", "| Concurrent | Requests | Errors | RPS | p50 ms | p95 ms | p99 ms |", "|---:|---:|---:|---:|---:|---:|---:|"]
    for row in result["concurrency"]:
        lines.append("| {0} | {1} | {2} | {3:.2f} | {4:.2f} | {5:.2f} | {6:.2f} |".format(row["concurrency"], row["requests"], row["errors"], row["rps"], row["p50_ms"], row["p95_ms"], row["p99_ms"]))
    lines += ["", "## Phase 3 — Multi-tenant isolation", "", "- Checks: " + str(result["isolation"]["checks"]), "- Violations: " + str(result["isolation"]["violations"]), "", "## Phase 4 — Durable worker stress/recovery", ""]
    if result["durable"]["supported"]:
        for k, v in result["durable"].items():
            if k != "supported": lines.append("- " + k.replace("_", " ").title() + ": " + str(v))
    else:
        lines.append("- Unsupported in this run: PostgreSQL durable-job environment was not configured.")
    lines += ["", "## Limitations", ""]
    lines.extend("- " + str(x) for x in result["limitations"])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

async def request_many(app, headers: dict[str, str], total: int, concurrency: int) -> dict[str, Any]:
    import httpx
    latencies, errors, status_counts = [], 0, {}
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://capacity.local") as client:
        async def one():
            nonlocal errors
            async with sem:
                started = time.perf_counter()
                try:
                    response = await client.get("/v1/jobs?limit=1", headers=headers)
                    latencies.append((time.perf_counter() - started) * 1000)
                    status_counts[str(response.status_code)] = status_counts.get(str(response.status_code), 0) + 1
                    if response.status_code != 200: errors += 1
                except Exception:
                    errors += 1
        started = time.perf_counter()
        await asyncio.gather(*(one() for _ in range(total)))
        elapsed = time.perf_counter() - started
    return {"concurrency": concurrency, "requests": total, "errors": errors, "rps": total / elapsed if elapsed else 0,
            "p50_ms": percentile(latencies, 50) or 0, "p95_ms": percentile(latencies, 95) or 0,
            "p99_ms": percentile(latencies, 99) or 0, "status_counts": status_counts, "duration_s": elapsed}

def run() -> int:
    started = datetime.now(timezone.utc)
    revision = os.getenv("GITHUB_SHA", "local")
    db_url = os.getenv("DATABASE_URL") or os.getenv("OAE_POSTGRES_TEST_URL", "")
    if db_url: os.environ["DATABASE_URL"] = db_url

    from fastapi.testclient import TestClient
    from oae.api.app import app
    from oae.api.config import settings
    from oae.api.db import db
    from oae.api.durable_jobs import DurableJobRepository
    from oae.api.migrations import apply_postgres_migrations, migration_files

    result = {"revision": revision, "started_at": started.isoformat(),
              "runtime": {"python": platform.python_version(), "platform": platform.platform(), "database_backend": settings.database_backend},
              "baseline": [], "concurrency": [], "isolation": {"checks": 0, "violations": 0},
              "durable": {"supported": False}, "gates": {"isolation_violation": False, "silent_job_loss": False, "stuck_jobs": False}, "limitations": []}

    with TemporaryDirectory(prefix="oae-capacity-") as tmp:
        if settings.database_backend == "sqlite":
            settings.database_url = "sqlite:///" + str(Path(tmp) / "capacity.db")
        elif settings.database_backend == "postgres":
            # Bootstrap the legacy/base PostgreSQL tables through the same adapter used by the API
            # before applying ordered feature migrations that reference tenants/jobs.
            with db():
                pass
            import psycopg
            with psycopg.connect(settings.resolved_database_url) as conn:
                apply_postgres_migrations(conn, migration_files())
        settings.durable_jobs_enabled = settings.database_backend == "postgres"
        settings.realtime_events_enabled = False
        settings.worker_authorization_enforcement_enabled = False
        settings.api_control_rate_limit_per_minute = max(settings.api_control_rate_limit_per_minute, 100000)
        client = TestClient(app)

        def timed(method, path, **kwargs):
            started = time.perf_counter()
            response = client.request(method, path, **kwargs)
            return response, (time.perf_counter() - started) * 1000

        response, latency = timed("GET", "/health")
        result["baseline"].append({"operation": "/health", "status_code": response.status_code, "latency_ms": latency})
        tenant_response, latency = timed("POST", "/v1/tenants", json={"name": "capacity-baseline"})
        if tenant_response.status_code != 201: raise RuntimeError("Tenant setup failed: " + tenant_response.text)
        tenant = tenant_response.json()
        headers = {"Authorization": "Bearer " + tenant["api_key"]}
        result["baseline"].append({"operation": "POST /v1/tenants", "status_code": tenant_response.status_code, "latency_ms": latency})

        repo_response, latency = timed("POST", "/v1/repositories", headers=headers, json={"provider": "github", "external_id": "Olori24/oae-core", "clone_url": "https://github.com/Olori24/oae-core.git"})
        if repo_response.status_code != 201: raise RuntimeError("Repository setup failed: " + repo_response.text)
        result["baseline"].append({"operation": "POST /v1/repositories", "status_code": repo_response.status_code, "latency_ms": latency})

        job_response, latency = timed("POST", "/v1/jobs", headers=headers, json={"operation": "capacity_probe", "payload": {"probe": True}, "idempotency_key": "capacity-baseline-job"})
        if job_response.status_code != 202: raise RuntimeError("Job setup failed: " + job_response.text)
        job_id = job_response.json()["id"]
        result["baseline"].append({"operation": "POST /v1/jobs", "status_code": job_response.status_code, "latency_ms": latency})
        get_response, latency = timed("GET", "/v1/jobs/" + job_id, headers=headers)
        result["baseline"].append({"operation": "GET /v1/jobs/{id}", "status_code": get_response.status_code, "latency_ms": latency})

        for level in env_levels():
            row = asyncio.run(request_many(app, headers, level, level))
            result["concurrency"].append(row)
            if row["errors"] >= max(1, level // 2):
                result["limitations"].append("Stopped concurrency progression at " + str(level) + " after >50% errors.")
                break

        other_response, _ = timed("POST", "/v1/tenants", json={"name": "capacity-other"})
        if other_response.status_code != 201: raise RuntimeError("Second tenant setup failed: " + other_response.text)
        other_headers = {"Authorization": "Bearer " + other_response.json()["api_key"]}
        repo_id = repo_response.json()["id"]
        checks = [("job", client.get("/v1/jobs/" + job_id, headers=other_headers).status_code),
                  ("repository", client.get("/v1/repositories/" + repo_id + "/revisions", headers=other_headers).status_code)]
        violations = sum(status not in (403, 404) for _, status in checks)
        result["isolation"] = {"checks": len(checks), "violations": violations, "statuses": dict(checks)}
        result["gates"]["isolation_violation"] = violations > 0

        if settings.database_backend == "postgres":
            result["durable"]["supported"] = True
            repository = DurableJobRepository()
            worker_id = repository.register_worker(worker_name="capacity-lab-" + tenant["tenant_id"])
            batch = 100
            with ThreadPoolExecutor(max_workers=16) as pool:
                futures = [pool.submit(repository.enqueue, tenant_id=tenant["tenant_id"], operation="analyze", payload={"i": i}, idempotency_key="capacity-batch-" + str(i)) for i in range(batch)]
                jobs = [f.result() for f in futures]
            claimed, claim_lock = [], __import__("threading").Lock()
            def claim():
                while True:
                    lease = repository.claim_next(worker_id)
                    if lease is None: return
                    with claim_lock: claimed.append(lease)
            with ThreadPoolExecutor(max_workers=8) as pool: list(pool.map(lambda _: claim(), range(8)))
            with ThreadPoolExecutor(max_workers=16) as pool: list(pool.map(lambda lease: repository.complete(lease, {"ok": True}), claimed))
            with db() as conn:
                completed = conn.execute("SELECT COUNT(*) FROM jobs WHERE tenant_id=? AND status='completed' AND operation='capacity_batch'", (tenant["tenant_id"],)).fetchone()[0]
            result["durable"].update({"enqueued": len(jobs), "claimed": len(claimed), "completed": completed, "lost": batch - completed,
                                      "duplicate_delivery": len(claimed) - len({lease.job_id for lease in claimed})})
            result["gates"]["silent_job_loss"] = completed != batch
            result["gates"]["stuck_jobs"] = completed != batch
            idem_a = repository.enqueue(tenant_id=tenant["tenant_id"], operation="analyze", payload={"same": True}, idempotency_key="capacity-idempotent")
            idem_b = repository.enqueue(tenant_id=tenant["tenant_id"], operation="analyze", payload={"same": True}, idempotency_key="capacity-idempotent")
            result["durable"]["idempotency_same_job"] = idem_a.id == idem_b.id and idem_a.created and not idem_b.created
            interrupted = repository.enqueue(tenant_id=tenant["tenant_id"], operation="analyze", payload={"interrupted": True}, idempotency_key="capacity-interrupted")
            interrupted_lease = repository.claim_next(worker_id)
            if interrupted_lease is None or interrupted_lease.job_id != interrupted.id: raise RuntimeError("Could not claim interruption test job.")
            with db() as conn:
                conn.execute("UPDATE jobs SET lease_expires_at=? WHERE id=? AND tenant_id=?", (datetime.now(timezone.utc) - timedelta(seconds=5), interrupted.id, tenant["tenant_id"]))
            recovered = repository.recover_expired_leases()
            retry_lease = repository.claim_next(worker_id)
            if retry_lease is not None: repository.complete(retry_lease, {"recovered": True})
            result["durable"]["expired_lease_recovered"] = recovered
            result["durable"]["recovery_reclaimed_and_completed"] = bool(retry_lease)
        else:
            result["limitations"].append("Phase 4 requires PostgreSQL and was not executed in this run.")
        result["resources"] = process_resources()

    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    result["duration_s"] = (datetime.fromisoformat(result["finished_at"]) - started).total_seconds()
    RESULTS.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    make_report(result)
    print(json.dumps(result, indent=2, default=str))
    return 1 if any(result["gates"].values()) else 0

if __name__ == "__main__":
    raise SystemExit(run())
