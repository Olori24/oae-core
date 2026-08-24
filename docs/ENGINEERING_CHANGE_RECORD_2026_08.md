# OAE Engineering Change Record: August 2026

## Purpose and evidence boundary

This record consolidates the repository work completed through the production-platform hardening programme. It distinguishes implemented and validated controls from controls that require a real deployment host, shared production dependencies, or measured workload evidence. It should be read with the [production-platform baseline](PRODUCTION_PLATFORM_MANDATE_BASELINE.md) and the [Phase 2 real-host validation procedure](REAL_HOST_PHASE_2_VALIDATION.md).

## Completed delivery record

| Delivery area | Completed engineering work | Evidence retained in the repository | Current boundary |
|---|---|---|---|
| Tenant control plane | Added tenant-scoped repository, revision, workspace, job, artifact, and realtime ownership checks. Cross-tenant lookups resolve empty or not found. | API, workspace, durable-job, realtime, and integration regression tests. | Every new tenant-owned aggregate still requires adversarial isolation coverage. |
| Repository and workspace lifecycle | Added repository registration, immutable revision pins, PostgreSQL workspace provisioning, quota reservation, manifesting, retention, and cleanup-on-failure. | `0001_workspace_foundation.sql`, workspace manager tests, and repository API tests. | Shared storage isolation and failure handling require a representative production-store exercise. |
| Durable job execution | Added PostgreSQL job leases, heartbeats, attempt records, retry backoff, stale-lease recovery, and fenced claims. | `0002_durable_job_worker_foundation.sql`, durable-job tests, and worker modules. | Durable mode must not be enabled until PostgreSQL migrations and worker health checks are complete. |
| Transactional event delivery | Added transactional outbox writes, relay leasing, ordered replay records, authenticated SSE, cursor recovery, snapshots, and Caddy anti-buffering configuration. | `0003_transactional_outbox_sse.sql`, `0004_realtime_event_metadata.sql`, relay tests, and the event-delivery runbook. | Fan-out, slow-consumer, reconnect, and capacity behavior need real-host measurement. |
| Production topology | Added a five-service Compose topology, private API port policy, Caddy gateway, staging ACME configuration, environment templates, and handoff procedure. | `docker-compose.production.yml`, `Caddyfile`, `Caddyfile.staging`, and deployment documentation. | Docker, DNS, cloud firewall, ACME, real secrets, and host health have not run in this sandbox. |
| Developer governance | Added PR and issue templates, collaboration guidance, contribution evidence practices, and a focused README entry point. | `.github/`, `docs/DEVELOPER_COLLABORATION.md`, `CONTRIBUTING.md`, and README. | Review policy still requires human maintainers in the target repository. |
| Worker authorization foundation | Added tenant-scoped authorization records, expiry, durable audit events, a job authorization reference, and optional durable-worker enforcement. | `0005_worker_authorization_foundation.sql`, `worker_authorizations.py`, and focused authorization tests. | No live authority is implied until PostgreSQL staging validation and feature-flag activation are complete. |
| Principal roles and separation of duties | Added owner, operator, approver, and viewer API-key roles. Owners can issue and revoke separate principal keys; requesters cannot self-approve authorizations. | `0006_principal_and_authorization_decision_metadata.sql`, principal-key tests, and authorization lifecycle tests. | Role claims are API-key based. Enterprise identity federation, policy evaluation, and role administration workflows remain future work. |
| API inventory hardening | Replaced fixed list caps with opaque cursors for repository, revision, workspace, and job inventories. | API pagination regression coverage and `X-Next-Cursor` contract. | Cursors are API-level controls and do not replace storage-index capacity measurement. |
| Control-write rate protection | Added bounded process-local limits and `429` responses with `Retry-After` for tenant creation, key lifecycle, authorization decisions, and job submission. | `rate_limits.py` and unit coverage. | This is not distributed rate limiting. Horizontal deployments require equivalent edge or shared-store enforcement. |

## Verified repository quality state

The final local validation for this delivery reported **851 passing tests**, **4 skipped PostgreSQL integration tests**, **81.32% source coverage** against the enforced 70% minimum, a clean Ruff run, clean mypy analysis across 325 source files, and a clean `git diff --check`. The only emitted warning is FastAPI TestClient deprecation from the installed dependency stack. This evidence validates the repository state; it does not certify public traffic, production capacity, or recovery operations.

## Deliberate non-claims

OAE does not currently claim 100,000-user capacity, production TLS completion, backup restoration success, distributed rate limiting, unrestricted autonomy, enterprise identity federation, or a complete commercial billing system. Those claims require measured evidence and deployment-specific validation, not source inspection alone.

## Next governed execution sequence

The next execution sequence is intentionally operational rather than speculative. Run the staging procedure in [Phase 2 real-host validation](REAL_HOST_PHASE_2_VALIDATION.md); complete the Caddy staging certificate transaction; exercise approval, revocation, enforcement, pagination, and rate-limit behavior with PostgreSQL; perform a backup restoration drill; measure worker, relay, and SSE capacity; and only then choose SLOs and production feature-flag values.
