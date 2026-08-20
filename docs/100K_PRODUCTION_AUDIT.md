# OAE 100K Production Audit

**Audit target:** `main`

**Audit mode:** evidence-first production readiness review

**Target:** reliably onboard and sustain 100,000 users

**Current verdict:** RED — NOT READY

## Executive finding

OAE has a substantially stronger production foundation than a simple local FastAPI prototype: the repository contains PostgreSQL migrations, durable job leasing, transactional outbox/SSE infrastructure, Docker production topology, tenant-scoped persistence, API-key authentication, and automated quality gates.

That is not evidence of 100,000-user capacity.

The current implementation has several hard capacity risks that must be addressed before a 100K claim is credible.

## Evidence classification

- **MEASURED:** only when an executable benchmark has produced a recorded result.
- **ESTIMATED:** derived from architecture/configuration, not a benchmark.
- **UNKNOWN:** requires a live/staging environment or runtime telemetry.

No fabricated capacity numbers are recorded in this document.

## Findings

### P0 — PostgreSQL connections are created per database context

**Status:** OPEN

`src/oae/api/db.py` calls `psycopg.connect(settings.resolved_database_url)` for every PostgreSQL `db()` context and closes the connection at the end of the context.

The API authentication path itself performs a database operation, and ordinary authenticated requests perform additional database operations. Under concurrent traffic this makes connection establishment and database `max_connections` a direct scaling boundary.

**Evidence:** `src/oae/api/db.py`

**Required remediation:** introduce a process-local bounded PostgreSQL connection pool, expose pool size/timeout as configuration, instrument pool wait time, and size the aggregate pool across API/worker/relay processes against the actual PostgreSQL connection budget.

**Why this matters:** PostgreSQL connections are a finite server resource; a pool exists specifically to control concurrent connections and avoid repeated connection setup. See the Psycopg pooling guidance: https://www.psycopg.org/psycopg3/docs/advanced/pool.html.

### P0 — Authentication performs PBKDF2 work on every authenticated request

**Status:** OPEN

`require_tenant()` selects candidate API keys and calls PBKDF2-SHA256 with 310,000 iterations for every candidate on every authenticated request.

The key prefix limits candidate rows, which is good, but successful authentication still requires a deliberately expensive password-hash computation on each request. At high request rates this moves authentication into a CPU scaling boundary and creates an attractive application-layer denial-of-service target.

**Evidence:** `src/oae/api/auth.py`

**Required remediation:** retain a strong offline-resistant verifier, but introduce a fast keyed lookup/fingerprint and a bounded short-lived authentication result cache that never stores the plaintext API key. Measure CPU cost and authentication throughput before/after.

### P0 — SSE implementation performs periodic database polling per connection

**Status:** OPEN

The SSE stream sleeps and calls the event store repeatedly when no events are available. Default polling is one second.

This architecture is acceptable at small beta scale but is not evidence for 100,000 simultaneously connected clients. If 100,000 clients remain connected and idle, the implementation can create an extremely large amount of repeated database polling even when no events exist.

**Evidence:** `src/oae/api/routes.py`, `sse_poll_seconds=1.0` in `src/oae/api/config.py`.

**Required remediation:** move live delivery to a broker/pub-sub or a bounded shared Postgres listener layer. A client connection must not map one-for-one to a database polling loop.

### P0 — Worker throughput is serialized per worker process

**Status:** OPEN

`DurableWorker.run_once()` claims one job and executes it synchronously before claiming another job. The production Compose topology defines one worker service instance by default.

The durable queue can be horizontally scaled, but the repository currently provides no measured worker throughput, no concurrency target, and no evidence that the underlying engineering operations are safe for concurrent execution.

**Evidence:** `src/oae/api/durable_worker.py`, `docker-compose.production.yml`.

**Required remediation:** establish measured jobs/sec by operation, define worker concurrency, prove workspace isolation and execution safety, then scale workers horizontally against queue depth and downstream API limits.

### P1 — Production topology is single-host Compose, not demonstrated horizontal infrastructure

**Status:** OPEN

The production file defines PostgreSQL, API, worker, relay, migration and Caddy on one Compose deployment. This is a useful production baseline but does not by itself demonstrate multi-instance API scaling, shared durable workspace storage across hosts, database failover, or automated recovery.

**Evidence:** `docker-compose.production.yml`.

**Required remediation:** document and validate the actual deployment target, then test at least two API instances, multiple workers, relay redundancy, shared storage semantics, database backup/restore, and failure recovery.

### P1 — No 100K load test evidence is currently present

**Status:** OPEN

Repository search did not identify an existing 100K-capacity load-test suite. Automated tests are valuable correctness gates but cannot substitute for measured concurrency, latency, throughput and saturation results.

**Required remediation:** add a controlled load-test harness and run it against an isolated production-like environment.

### P1 — Tenant isolation is implemented in query predicates but needs adversarial integration proof

**Status:** PARTIALLY VERIFIED

The visible API routes consistently pass the authenticated tenant ID into repository/job queries. Examples include job lookup and repository revision ownership checks.

This is strong implementation evidence, not proof. A cross-tenant integration test must attempt IDOR-style access using tenant B credentials against tenant A's jobs, repositories, revisions, workspaces and event streams.

### P1 — Production configuration has safe explicit values in the committed example

**Status:** VERIFIED BY INSPECTION

The production environment example explicitly sets `APP_ENV=production`, `ALLOWED_HOSTS`, `CORS_ORIGINS`, PostgreSQL configuration, durable jobs and realtime events. Wildcard defaults remain in application configuration for development fallback, so deployment validation must ensure production never starts with missing host/CORS restrictions.

## Positive controls already present

- Tenant-scoped records and ownership predicates.
- One-time API key issuance with salted PBKDF2 storage.
- Durable PostgreSQL job leasing with `FOR UPDATE SKIP LOCKED`.
- Lease-token fencing for job completion/retry operations.
- Retry limits and lease recovery.
- Transactional event/outbox architecture.
- Cursor-based event replay and snapshot recovery.
- Production gateway keeps the API container port private.
- JSON logging and Sentry integration hooks.
- Dependency, static-analysis and coverage gates are part of the stated quality process.

## 100K test matrix

The following must be executed against a production-like environment before the final verdict:

| Stage | Users | Required evidence |
|---|---:|---|
| Smoke | 100 | end-to-end correctness + baseline latency |
| Load | 1,000 | throughput + p50/p95/p99 + errors |
| Load | 5,000 | saturation trend |
| Load | 10,000 | acquisition spike behaviour |
| Load | 25,000 | database/worker/queue limits |
| Load | 50,000 | sustained workload + recovery |
| Target | 100,000 | sustained workload + failure injection |

The stages must use realistic workflows, not a single health endpoint.

## Required measurements

- concurrent active users
- requests/sec
- successful requests/sec
- p50/p95/p99 latency
- HTTP error rate
- authentication CPU cost
- API CPU/memory
- PostgreSQL connections/utilization/locks/query latency
- queue depth and oldest queued job age
- worker throughput and utilization
- SSE connection count and event delivery latency
- external API rate-limit consumption
- retry amplification
- storage usage

## Current final verdict

**STATUS: RED — NOT READY**

**VERIFIED CAPACITY:** UNKNOWN

**PERFORMANCE:** UNKNOWN — no controlled 100K runtime benchmark has been executed in this audit environment.

**100K VERDICT:** PLAUSIBLE BUT UNTESTED

The architecture contains several necessary production components, but the current code contains clear scaling boundaries around database connection management, per-request PBKDF2 authentication cost, SSE polling, and worker throughput. Those boundaries must be fixed and measured before a GREEN verdict.

## First failure hypothesis

The most likely first failure under a large sudden traffic event is **database pressure caused by connection establishment plus authentication/database work**, followed closely by **SSE polling amplification** if a large percentage of users maintain live event streams.

This is a hypothesis based on inspected code, not a measured production result.

## Next engineering gates

1. Bound and instrument PostgreSQL connection usage.
2. Reduce authentication CPU amplification without weakening key security.
3. Replace per-client SSE polling with shared event distribution.
4. Establish measured worker throughput and horizontal worker scaling.
5. Add adversarial tenant-isolation integration tests.
6. Add controlled load testing and record measured results.
7. Run failure-injection tests.
8. Re-run the complete audit and only then consider changing the verdict.
