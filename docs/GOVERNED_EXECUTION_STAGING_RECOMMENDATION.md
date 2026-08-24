# Governed Execution Staging Recommendation

## Recommended path

Use a **separate, disposable staging server with root-level Docker control, a public static IP, and a dedicated staging hostname**. This is the most reliable path for OAE because its evidence path requires Docker Compose, PostgreSQL, Caddy, a durable worker, an outbox relay, public HTTP and HTTPS reachability, and the ability to inspect service telemetry together. A frontend-only managed deployment cannot substitute for this validation because it does not exercise the Python worker, PostgreSQL lease semantics, Caddy edge policy, or real network boundary.

Do not start on the eventual production hostname. Use a distinct staging API hostname and Let’s Encrypt’s staging issuer. Keep PostgreSQL and the API's port 8000 private to the Compose network. Only Caddy should receive host access to TCP 80 and 443.

## Minimum host gate

| Requirement | Required state before validation | Reason |
|---|---|---|
| Operating system control | A maintained Ubuntu or equivalent server with root or sudo access | Docker, firewall, service logs, and filesystem permissions need host-level control. |
| Runtime | Docker Engine and Docker Compose installed and verified | The committed topology is Compose-based. |
| Network | One staging DNS record resolves to the host; inbound TCP 80 and 443 are open | Caddy must complete a staging ACME transaction and serve the HTTPS edge. |
| Private services | PostgreSQL and API port 8000 are not publicly reachable | The gateway is the only intended public entry point. |
| Secrets | Environment file is present with generated secrets and exact staging CORS origin | Authorization, API-key hashing, database access, and edge behavior depend on these settings. |
| Telemetry access | Redacted access to Caddy, API, worker, relay, migration, and PostgreSQL logs | A control cannot be validated only from an HTTP response. |

## Ordered validation sequence

Begin with the staging Caddy procedure. Confirm the hostname, gateway reachability, and staging certificate transaction before enabling durable execution. Apply migrations through `0006_principal_and_authorization_decision_metadata.sql`, then start the API, worker, relay, and gateway with durable jobs and realtime events enabled. Keep `WORKER_AUTHORIZATION_ENFORCEMENT_ENABLED=false` until the principal and authorization checks have been observed successfully.

Create a staging tenant with the initial owner principal. Using that owner, issue a separate operator key and a separate approver key. Verify that the operator can request a build authorization but receives `403` if attempting approval. Verify that an approver cannot request execution authority. Verify that self-approval is rejected, then approve using a distinct approver and preserve the resulting redacted authorization trace.

Next, enable worker-authorization enforcement. Prove that a build request without an active authorization is denied, and separately prove rejection for revoked, expired, cross-tenant, and wrong-operation authorizations. Then submit one approved, tenant-matching build job and confirm a durable worker claim, attempt record, outbox event, relay projection, and authenticated event delivery. Revoke a second approval before claim and prove that no worker can claim the associated job.

Finally, walk the cursor pagination path across more than one page of repositories, revisions, workspaces, and jobs. Confirm no duplicate or cross-tenant records. Exercise the selected control-write budget until `429` with `Retry-After: 60` is observed. Treat that result as process-local protection only, not a horizontal-scale rate-limit certification.

## Telemetry evidence record

Capture each validation event as a redacted row with the following fields: UTC timestamp, trace or correlation identifier, service name, control under test, tenant pseudonym, authorization pseudonym, job pseudonym, HTTP status or worker state, outbox or event identifier, elapsed time, and pass or fail outcome. Preserve a short redacted excerpt from the gateway, API, worker, relay, migration, and PostgreSQL evidence for the same trace. Never retain plaintext API keys, passwords, private keys, certificate material, full request bodies, or full raw logs in OAE tables.

## Activation hold points

Do not enable governed build execution in a shared or production environment if any of the following is missing: an applied migration ledger through `0006`; separate owner, operator, and approver principals; proven self-approval denial; proven revocation before worker claim; a private API and database boundary; staging ACME evidence; durable outbox and SSE trace evidence; a backup-restore result; or an edge or shared-store rate-limit design for any horizontally scaled API deployment.

The above process establishes the first real-host evidence for governed execution. It is not a capacity certification. Worker, relay, database, and SSE load must still be measured on representative infrastructure before making concurrency, latency, availability, or 100,000-user claims.
