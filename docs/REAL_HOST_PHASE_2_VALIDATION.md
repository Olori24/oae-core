# Phase 2 Real-Host Validation

## Purpose

This procedure validates the repository-safe controls delivered in the second production-platform phase. It does not authorize a production release by itself. Run it only on an isolated staging host after PostgreSQL, Caddy, DNS, firewall, and secret-management controls from the existing production handoff have been completed.

## Migration and configuration gate

Apply migrations through `0006_principal_and_authorization_decision_metadata.sql` on the staging PostgreSQL database. Confirm that the migration ledger records both `0005_worker_authorization_foundation.sql` and `0006_principal_and_authorization_decision_metadata.sql` exactly once. Confirm that the deployed process uses PostgreSQL, durable jobs, and realtime delivery as intended. Do not set `WORKER_AUTHORIZATION_ENFORCEMENT_ENABLED=true` until the approval-path checks below have passed.

## Principal and approval-path validation

Create a staging tenant and retain its initial owner API key only in the approved secret store. Use that owner key to issue a separate `operator` principal key and a separate `approver` principal key. Verify that an operator can create a pending build authorization, but receives `403` when attempting to approve it. Verify that an approver cannot create a new execution authorization. Verify that an approver distinct from the requester can approve the request and that the authorization read model records the principal identifiers and role metadata.

Attempt self-approval using the requester principal. The operation must fail with a conflict response and no valid authorization event. Revoke an approved authorization before a worker claim, then verify that a subsequent build claim is blocked when enforcement is enabled. Query the durable outbox and realtime event projection to confirm that `authorization.requested`, `authorization.approved`, and `authorization.revoked` are tenant-scoped and in order.

## Worker enforcement validation

With `WORKER_AUTHORIZATION_ENFORCEMENT_ENABLED=true`, submit a build job without an authorization reference and verify that the API returns `403`. Submit a build job with an expired, revoked, cross-tenant, wrong-operation, or rejected authorization and verify the same denial. Submit a build job with an active, approved, tenant-matching authorization and verify that the durable worker can claim it. Expire or revoke the authorization before a second claim and verify that no worker can claim the job.

## Pagination and rate-limit validation

Create more than one page of repositories, revisions, workspaces, and jobs in the staging tenant. Read each route with a bounded `limit` and its `X-Next-Cursor` value. Confirm that every item appears once, no cross-tenant item appears, and a malformed cursor returns `422`. Exercise the selected write endpoints until the configured per-minute process limit returns `429` with `Retry-After: 60`.

> The delivered limiter is deliberately process-local. It is effective for single-process protection and development but is not a distributed rate-limit solution. Before horizontally scaling the API, enforce equivalent or stricter tenant and origin limits at the edge or through a shared store.

## Evidence to retain

Retain the staging migration ledger, redacted request and response samples, authorization event identifiers, worker attempt identifiers, cursor walk results, rate-limit results, service version, and operator sign-off. Do not retain raw API keys, credentials, private keys, unredacted request payloads, or full host logs in the application database.
