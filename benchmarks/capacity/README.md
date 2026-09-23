# OAE Core Capacity Lab

## Objective

Execute Phases 1–4 as one integrated capacity task:

1. Baseline
2. Concurrency
3. Multi-tenant isolation stress
4. Durable-worker stress/recovery

This benchmark must report measured results only. No fabricated capacity claims.

## Execution contract

The benchmark must:
- run locally and in CI without uploading source code;
- use existing test/application interfaces where possible;
- use PostgreSQL 16 for durable-job tests;
- record runtime, revision, test commands, load profile, latency percentiles, throughput, error rate, queue/worker behavior, and recovery outcomes;
- fail closed on security/isolation violations;
- distinguish unsupported measurements from zero failures;
- produce machine-readable JSON plus a human-readable Markdown report;
- avoid destructive production actions.

## Phases

### Phase 1 — Baseline
Measure health/API latency, authentication and tenant setup, repository registration, mission/job creation/retrieval, event/SSE behavior, PostgreSQL persistence, and compile/test/lint/typecheck gates.

### Phase 2 — Concurrency
Progressively test 10, 25, 50, 100, 250, 500, and 1,000 concurrent operations, stopping when the environment cannot safely continue. Measure RPS, p50/p95/p99 latency, errors, CPU/memory, PostgreSQL connections, queue depth, worker throughput, completion time, retries, and timeouts.

### Phase 3 — Multi-tenant isolation
Under concurrent load, verify tenants cannot access another tenant's jobs, repositories, workspaces, events/SSE streams, or authorization-controlled resources. Include negative authorization tests. Any cross-tenant exposure is a hard failure.

### Phase 4 — Durable worker stress/recovery
Submit a controlled batch of durable jobs and test leasing, heartbeats, completion, retries, duplicate delivery/idempotency, stale lease recovery, worker interruption, safe database interruption/reconnection where injectable, and outbox/event recovery. Record lost, duplicated, stuck, retried, and recovered jobs.

## Output

Generate:
- benchmarks/capacity/results.json
- benchmarks/capacity/CAPACITY_REPORT.md
- benchmarks/capacity/README.md

The report must include exact commands, environment, commit SHA, timestamps, measurements, limitations, and conclusions strictly supported by measurements.

## Acceptance gates

- No security/isolation violation.
- No silent job loss.
- No unbounded stuck jobs within the benchmark timeout.
- Existing repository CI gates remain green.
- Benchmark itself is reproducible.


## Harness

`run_capacity_lab.py` executes the integrated baseline, concurrency, isolation, and durable-worker checks. CI runs it against PostgreSQL 16 and uploads measured JSON/Markdown artifacts.
