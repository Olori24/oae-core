## Change summary

Explain the user or operator outcome in a few sentences. State whether this changes the API, tenant boundary, durable job flow, workspace lifecycle, event delivery, deployment topology, or documentation.

## Evidence

- [ ] Focused tests cover the changed behavior and failure path.
- [ ] `ruff check src tests scripts` passed.
- [ ] `mypy src` passed when Python source changed.
- [ ] The full coverage gate ran for a broad or production-facing change.
- [ ] `git diff --check` passed.

## Boundary review

- [ ] Tenant-owned reads and writes are constrained by `tenant_id`.
- [ ] Credentials are not stored, logged, or returned; only external `credential_ref` values are used where required.
- [ ] New client-visible behavior distinguishes live data from sample or simulated data.
- [ ] Durable jobs, outbox writes, and SSE changes preserve retry, replay, and idempotency behavior.
- [ ] Deployment or configuration changes retain the rule that only Caddy exposes public ports 80/443.

## Operational impact

Describe migrations, feature flags, deployment ordering, rollback behavior, CORS requirements, or monitoring changes. Write **None** when there is no operational impact.

## Screens or traces

Attach a concise API response, test result, log excerpt with secrets removed, or frontend screenshot when it helps a reviewer verify the behavior.
