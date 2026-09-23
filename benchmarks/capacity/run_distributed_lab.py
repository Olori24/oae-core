#!/usr/bin/env python3
"""Network-level OAE capacity probe.

Usage:
  OAE_BASE_URL=https://example.com python benchmarks/capacity/run_distributed_lab.py

This intentionally targets a real HTTP server rather than ASGI in-process transport.
It measures the public health endpoint so the result reflects network/server concurrency.
"""
from __future__ import annotations

import asyncio
import json
import os
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

LEVELS = [int(x) for x in os.getenv("OAE_DISTRIBUTED_LEVELS", "10,25,50,100,250,500").split(",") if x]
BASE_URL = os.environ.get("OAE_BASE_URL", "").rstrip("/")
TIMEOUT = float(os.getenv("OAE_HTTP_TIMEOUT_S", "60"))
PATH = os.getenv("OAE_PROBE_PATH", "/health")

if not BASE_URL:
    raise SystemExit("OAE_BASE_URL is required")


async def one(client: httpx.AsyncClient) -> tuple[float, int | None, str | None]:
    started = time.perf_counter()
    try:
        r = await client.get(f"{BASE_URL}{PATH}")
        return (time.perf_counter() - started, r.status_code, None)
    except Exception as exc:
        return (time.perf_counter() - started, None, type(exc).__name__)


async def run_level(level: int) -> dict:
    limits = httpx.Limits(max_connections=level, max_keepalive_connections=level)
    async with httpx.AsyncClient(timeout=TIMEOUT, limits=limits, follow_redirects=True) as client:
        started = time.perf_counter()
        samples = await asyncio.gather(*(one(client) for _ in range(level)))
        duration = time.perf_counter() - started

    latencies = sorted(x[0] * 1000 for x in samples)
    statuses: dict[str, int] = {}
    errors = 0
    for _, status, error in samples:
        if status is not None:
            statuses[str(status)] = statuses.get(str(status), 0) + 1
        else:
            errors += 1

    def pct(p: float) -> float:
        if not latencies:
            return 0.0
        idx = min(len(latencies) - 1, max(0, int((len(latencies) - 1) * p)))
        return round(latencies[idx], 3)

    return {
        "concurrency": level,
        "requests": level,
        "errors": errors,
        "rps": round(level / duration, 3) if duration else 0,
        "p50_ms": pct(0.50),
        "p95_ms": pct(0.95),
        "p99_ms": pct(0.99),
        "status_counts": statuses,
        "duration_s": round(duration, 3),
    }


async def main() -> None:
    results = [await run_level(level) for level in LEVELS]
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "path": PATH,
        "levels": LEVELS,
        "platform": platform.platform(),
        "python": sys.version,
        "results": results,
        "gates": {
            "http_errors": sum(x["errors"] for x in results) == 0,
            "non_2xx": sum(sum(v for k, v in x["status_counts"].items() if not k.startswith("2")) for x in results) == 0,
        },
        "limitations": [
            "Health endpoint only; this is network/server capacity, not a full authenticated write-path benchmark.",
            "Run against a deployed multi-worker topology for production evidence.",
        ],
    }
    Path("benchmarks/capacity/distributed-results.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if all(report["gates"].values()) else 1)


if __name__ == "__main__":
    asyncio.run(main())
