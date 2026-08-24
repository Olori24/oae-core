# OAE Production Platform Mandate Baseline

**Repository reviewed:** `dcc50cf`  
**Assessment date:** 24 August 2026  
**Scope:** Source, tests, local quality gates, committed deployment configuration, and documentation. This assessment does **not** certify a live environment, production traffic, public TLS, backup restoration, or capacity at any user scale.

## Verified baseline

The local quality baseline is healthy: 840 tests passed, 4 were skipped, coverage was 82.13% against a 70% threshold, Ruff passed, and mypy reported no issues across 323 source files. One FastAPI TestClient deprecation warning was emitted. These results establish code hygiene, not production capacity or operational readiness.

| Subsystem | Classification | Evidence observed | Material limitation or proof still required |
|---|---|---|---|
| Tenant API isolation | **Real, regression-tested** | Tenant-scoped repository, revision, workspace, and job queries are exercised in `tests/test_api.py`; cross-tenant access resolves empty or 404. | Extend adversarial coverage to all future mission, approval, ledger, memory, and SSE aggregates. |
| API-key verification and principals | **Partial, role-aware lifecycle added** | Salted PBKDF2-SHA256 hashes, constant-time comparison, bounded key length, revocation, owner-issued principal keys, and `owner`, `operator`, `approver`, and `viewer` roles are implemented in `src/oae/api/auth.py`. | A real-host secret-store workflow, key rotation ceremony, usage telemetry, and edge or distributed rate controls still require validation. |
| Repository registry and revision pinning | **Real, bounded control plane** | Tenant ownership, duplicate prevention, commit-shape validation, unsafe clone URL rejection, and secret-reference validation are tested. | Repository analysis and execution are not exposed as a fully governed end-to-end mission path. |
| Durable workspace provisioning | **Real for PostgreSQL-backed provisioning** | Advisory-lock quota reservation, immutable manifesting, tenant path partitioning, state transition fencing, outbox events, and cleanup-on-failure exist in `src/oae/api/workspace_manager.py`. | Workspace materialization is filesystem-based and has not been proven under production isolation, storage failure, or multi-host execution. |
| Durable job coordination | **Real for the PostgreSQL path** | Tenant idempotency, `SKIP LOCKED` claim, lease-token fencing, attempt records, heartbeat renewal, retry backoff, and expired-lease recovery are implemented in `src/oae/api/durable_jobs.py`. | The public API falls back to in-process background work unless durable jobs are explicitly enabled with PostgreSQL migrations. No production worker-scale measurement exists. |
| Transactional outbox and replay | **Real for the PostgreSQL path** | The relay leases records, preserves per-tenant order, persists replay records, and retries projection failures in `src/oae/api/outbox_relay.py`. | The feature is disabled by default; SSE is polling-based and unmeasured at production connection counts. |
| SSE client recovery | **Partial** | Replay, cursor expiry response, heartbeats, and Caddy anti-buffering configuration are committed. | No evidence yet for 100 to 100,000 concurrent connections, slow consumers, relay crash during real traffic, or host capacity. |
| Human approval and authorization | **Partial, governed lifecycle added** | PostgreSQL migrations `0005` and `0006` add tenant-scoped authorization records, role metadata, revocation facts, durable events, owner-issued approver identities, approver-only decision endpoints, self-approval denial, and optional worker-side enforcement for build operations. | Scope policy evaluation, separation-of-duties configuration beyond key roles, PostgreSQL integration proof, and operator runbook execution remain required before enabling real execution authority. |
| Autonomous engineering workflow | **Partial / unproven** | The repository contains many planner, executor, scanner, and recovery modules, but the current public API exposes only bounded `analyze`, `review`, `verify`, and `build` job operations. | No verified public workflow currently proves understand, plan, authorize, execute, verify, and record as one governed mission. |
| AI provider resilience and cost control | **Partial / unproven** | Provider abstractions exist. | No verified tenant budgets, provider circuit breaker, fallback policy, token accounting, cost control, or outage test evidence was established in this audit. |
| Security and input boundaries | **Partial** | Unsafe repository URL and secret-reference checks are covered; key hashes are not stored plaintext. | Rate limits, end-to-end prompt-injection controls, SSRF assessment, full IDOR coverage, execution sandbox enforcement, and real-host secret/log validation remain open. |
| Observability | **Partial** | Request IDs, JSON logging, and optional Sentry integration are present. | No metrics endpoint, production dashboard, alert policy, trace propagation guarantee, capacity telemetry, or operator SLO baseline is proven. |
| Production topology | **Partial, configuration-ready** | Compose keeps API port 8000 internal and exposes only Caddy on 80/443; Caddy uses `flush_interval -1` for SSE. | Docker, Caddy, DNS, firewall, ACME, secrets, migration, and real-host checks have not run in this sandbox. |
| API pagination and write-rate controls | **Partial, bounded controls added** | Repository, revision, workspace, and job inventories now support opaque tenant-scoped cursors; selected control writes have a bounded process-local limiter. | The limiter is not distributed and must be complemented by edge or shared-store controls before horizontal scaling. |
| Performance, capacity, and cost | **Unknown** | No measured authenticated load or SSE capacity evidence was reviewed. | No claim about 100,000 users, concurrency, throughput, latency, storage, or cost is justified until measured on representative infrastructure. |
| Backup and disaster recovery | **Unknown** | Runbook material exists. | No successful restore exercise was verified. |
| Billing, team lifecycle, and commercial entitlements | **Partial / absent from active API scope** | Basic tenant creation and API keys exist. | Plans, seats, suspension, data export/deletion controls, entitlement enforcement, and usage accounting need design and implementation. |

## Governing conclusion

OAE has a stronger foundation than a prototype in tenant-scoped registry data, PostgreSQL workspace and job primitives, transactional event delivery, and repository-level quality gates. It is **not** currently justified to claim 100,000-user readiness, unrestricted autonomy, live worker authorization, measured production resilience, backup readiness, or complete commercial SaaS operation.

The first implementation priority, a durable tenant-scoped authorization foundation, is now in place for the existing PostgreSQL durable-worker path. It records the tenant, requested operation, scope, requester, pending or decided state, expiry, decision actor, and durable audit event. It deliberately does **not** expose self-approval through the tenant API key. This reduces the highest-risk gap without pretending that role-aware approval, policy evaluation, or the broader scale mandate is complete.

## Controlled implementation sequence

1. Build the durable authorization boundary and worker-side enforcement with adversarial tenant and expiry tests.
2. Replace fixed list limits with cursor pagination and add request-scoped API rate limiting appropriate to the deployment edge.
3. Build an authenticated workload and failure-injection suite on real PostgreSQL, then establish SLOs from measurements.
4. Validate real-host topology, backup restore, TLS, firewall, SSE fan-out, and worker scaling before presenting a production capacity claim.
5. Add commercial entitlements, AI budgets, provider resilience, and complete governed mission orchestration only after the authorization boundary is enforced.
