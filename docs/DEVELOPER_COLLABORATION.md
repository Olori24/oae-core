# Developer Collaboration Guide

OAE is designed for contributors who can make engineering behavior more observable, bounded, recoverable, and tenant-safe. A useful change is not only code that passes locally; it includes enough tests, documentation, and operational context for another developer to reason about its behavior after the original author has moved on.

## Start with the operating boundary

Read the [README](../README.md), [CONTRIBUTING.md](../CONTRIBUTING.md), and [security policy](../SECURITY.md) before selecting work. The first question is not “what code can change?” but “what tenant-owned state, credential boundary, durable event, or deployment decision will this change affect?”

| Area | Collaboration expectation |
|---|---|
| API and database | Every owned row and read path must remain tenant-scoped. Schema changes need migration, compatibility, and rollback thinking. |
| Repository and workspace lifecycle | Preserve pinned revision lineage, quota reservation before storage commitment, and cleanup behavior on failure. |
| Durable execution | Job state, worker leases, retries, and terminal events must be inspectable and idempotent. |
| Realtime delivery | Outbox and SSE changes must keep ordered replay, cursor recovery, and explicit live-versus-simulated client labeling. |
| Deployment | Keep API port 8000 private; Caddy is the public TLS edge and must keep SSE forwarding unbuffered. |

## Development loop

Create a focused branch, keep the change small enough to review, and add the test closest to the changed boundary. Use the repository’s own quality gates before asking for review:

```bash
.venv/bin/pytest -q --cov=oae --cov-report=json:coverage.json
.venv/bin/python scripts/check_coverage_threshold.py --coverage-file coverage.json --threshold 70
.venv/bin/ruff check src tests scripts
.venv/bin/mypy src
.venv/bin/pip-audit
git diff --check
```

Run targeted PostgreSQL integration tests when the change involves migrations, leased claims, outbox projection, or SSE replay. The local suite may skip those tests without a configured PostgreSQL URL; CI provides a PostgreSQL service for the corresponding integration coverage.

## Review-ready pull requests

Use the repository pull-request template. Describe the observable change first, then the test evidence, then the operational impact. When behavior is live in the frontend, show a screenshot or a concise sanitized trace. When a deployment, migration, flag, or recovery action changes, link the relevant runbook section.

Do not use public issues for security reports. The issue forms route reproducible defects and bounded workflow proposals through the right review questions while keeping private credentials and sensitive tenant data out of the repository history.

## First contributions that help most

New contributors can start with test coverage for a tenant boundary, a small documentation correction verified against code, a focused API response improvement, or a deployment-regression test. Avoid broad refactors before understanding the durable job, workspace, and realtime-event design; reviewability is an OAE feature, not ceremony.
