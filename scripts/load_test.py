#!/usr/bin/env python3
"""Run a realistic OAE API load test against a deployed environment.

This harness never fabricates infrastructure metrics. It measures HTTP behavior only;
operator-supplied infrastructure metrics must be collected from the deployment.

Usage:
  python scripts/load_test.py --base-url https://api.example.com --keys-file keys.txt --users 100
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

import httpx


@dataclass
class Result:
    operation: str
    latency_ms: float
    status: int
    error: str | None = None


async def request(client: httpx.AsyncClient, method: str, path: str, headers: dict[str, str], **kwargs) -> Result:
    started = time.perf_counter()
    try:
        response = await client.request(method, path, headers=headers, **kwargs)
        return Result(path, (time.perf_counter() - started) * 1000, response.status_code)
    except Exception as exc:
        return Result(path, (time.perf_counter() - started) * 1000, 0, type(exc).__name__)


async def virtual_user(client: httpx.AsyncClient, api_key: str, index: int) -> list[Result]:
    headers = {"Authorization": f"Bearer {api_key}", "X-Request-ID": f"load-{index}"}
    results = [await request(client, "GET", "/v1/me", headers)]
    results.append(await request(client, "GET", "/v1/repositories?limit=25", headers))
    results.append(await request(client, "GET", "/health/ready", {}))
    return results


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    rank = (len(values) - 1) * p
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return values[low]
    return values[low] + (values[high] - values[low]) * (rank - low)


async def run(base_url: str, keys: list[str], users: int, timeout: float) -> dict[str, object]:
    if not keys:
        raise SystemExit("keys-file must contain at least one API key")
    if users < 1:
        raise SystemExit("users must be positive")

    limits = httpx.Limits(max_connections=max(users, 100), max_keepalive_connections=max(users, 100))
    async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout, limits=limits) as client:
        started = time.perf_counter()
        batches = [virtual_user(client, keys[i % len(keys)], i) for i in range(users)]
        nested = await asyncio.gather(*batches)
        elapsed = time.perf_counter() - started

    results = [item for batch in nested for item in batch]
    successful = [r for r in results if 200 <= r.status < 400]
    latencies = [r.latency_ms for r in results]
    errors = [r for r in results if r.status == 0 or r.status >= 500]
    by_operation: dict[str, dict[str, object]] = {}
    for result in results:
        entry = by_operation.setdefault(result.operation, {"count": 0, "errors": 0, "latencies_ms": []})
        entry["count"] = int(entry["count"]) + 1
        entry["latencies_ms"].append(result.latency_ms)
        if result.status == 0 or result.status >= 500:
            entry["errors"] = int(entry["errors"]) + 1

    for entry in by_operation.values():
        values = entry.pop("latencies_ms")
        entry["p50_ms"] = round(percentile(values, 0.50), 2)
        entry["p95_ms"] = round(percentile(values, 0.95), 2)
        entry["p99_ms"] = round(percentile(values, 0.99), 2)

    return {
        "classification": "MEASURED",
        "base_url": base_url,
        "virtual_users": users,
        "api_keys_used": len(keys),
        "elapsed_seconds": round(elapsed, 3),
        "requests": len(results),
        "successful_requests": len(successful),
        "error_requests": len(errors),
        "error_rate": round(len(errors) / len(results), 6) if results else 0,
        "requests_per_second": round(len(results) / elapsed, 2) if elapsed else 0,
        "p50_ms": round(percentile(latencies, 0.50), 2),
        "p95_ms": round(percentile(latencies, 0.95), 2),
        "p99_ms": round(percentile(latencies, 0.99), 2),
        "mean_ms": round(statistics.mean(latencies), 2) if latencies else 0,
        "by_operation": by_operation,
        "non_http_errors": [r.error for r in errors if r.error][:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--keys-file", type=Path, required=True)
    parser.add_argument("--users", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    keys = [line.strip() for line in args.keys_file.read_text().splitlines() if line.strip()]
    report = asyncio.run(run(args.base_url, keys, args.users, args.timeout))
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
