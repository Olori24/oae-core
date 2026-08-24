# Governed Execution Staging Evidence Record

## Scope

Use one record for each real-host governed-execution run. This record is evidence of a staging validation only. It does not establish production capacity, availability, backup recovery, distributed rate enforcement, or release approval.

| Field | Required value |
|---|---|
| Run identifier | An operator-created, non-secret identifier. |
| UTC window | Validation start and finish in UTC. |
| Deployed revision | Full Git commit SHA reported by `scripts/staging_preflight.py`. |
| Host posture | Disposable staging hostname, public TCP 80 and 443, private API and database boundary. |
| Operator sign-off | Named role and timestamp, without personal credentials. |
| Report location | Protected evidence location with its access policy. |

## Configuration gates

| Control | Expected evidence | Result: PASS, FAIL, or UNKNOWN | Redacted reference |
|---|---|---|---|
| Bootstrap preflight | Staging Compose configuration validates; placeholder secrets are rejected; port 8000 remains unexposed. |  |  |
| TLS edge | Caddy staging-ACME transaction, HTTPS health response, and SSE flush configuration. |  |  |
| Migration ledger | `0005_worker_authorization_foundation.sql` and `0006_principal_and_authorization_decision_metadata.sql` appear exactly once. |  |  |
| Durable activation | PostgreSQL, API, worker, and relay are healthy with durable jobs and realtime events enabled. |  |  |

## Governed execution controls

| Control | Expected result | Result: PASS, FAIL, or UNKNOWN | Redacted trace or event reference |
|---|---|---|---|
| Separate principals | Owner issues separate operator and approver principals. |  |  |
| Request authority | Operator creates a pending build authorization. |  |  |
| Self-approval denial | Requester approval attempt is denied and creates no approval event. |  |  |
| Approval | Different approver approves the matching tenant and operation. |  |  |
| Missing authorization | Enforced build request without authorization returns `403`. |  |  |
| Revocation | Revoked authorization cannot be claimed by a worker. |  |  |
| Valid claim | Active tenant-matching authorization permits one durable claim. |  |  |
| Event ordering | Requested, approved, and revoked outbox and realtime events are tenant-scoped and ordered. |  |  |
| Cursor isolation | Cursor walk emits every tenant item once and rejects malformed cursors with `422`. |  |  |
| Rate limit | Configured write budget yields `429` and `Retry-After: 60`. |  |  |

## Redaction rules

> Retain timestamps, service name, HTTP status, event or attempt pseudonym, and a short redacted excerpt. Do not retain raw bearer keys, passwords, private keys, database URLs containing credentials, cookies, full request bodies, certificate material, or unfiltered host logs.

Run `scripts/collect_staging_telemetry.py` from the connected staging host after the validation. Its evidence directory contains a sanitized service-status capture, per-service log excerpts, and aggregate migration and event summaries. Review every file manually before sharing it outside the protected operator evidence location.
