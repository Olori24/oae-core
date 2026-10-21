# Automation Engineering Standard

OAE workers, jobs, agents, and background automations must be controlled execution systems.

Required properties:
- explicit trigger and authority
- tenant/workspace scoping
- input validation
- idempotency for mutations
- bounded retries and backoff
- execution/correlation IDs
- persisted status transitions
- approval gates for consequential actions
- audit trail
- safe timeout/failure behavior
- provider isolation
- cost bounds where external services are used
- replay/recovery path

Unknown or unsafe operations must fail closed. Capacity claims must be supported by measured load and failure evidence.