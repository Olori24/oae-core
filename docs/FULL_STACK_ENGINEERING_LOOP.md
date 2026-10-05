# Full-Stack Engineering Loop

Mission 101 establishes the first governed repository engineering loop:

```text
registered repository
      ↓
pinned revision
      ↓
durable source workspace
      ↓
governed validation
      ↓
quality evidence
      ↓
readiness verdict
```

## API flow

1. Register a GitHub repository with `POST /v1/repositories`.
2. Pin a known commit with `POST /v1/repositories/{repository_id}/revisions`.
3. Request a build authorization with `POST /v1/worker-authorizations`.
4. Have an independent approver approve the authorization.
5. Materialize the pinned revision with `POST /v1/engineering/workspaces/provision`.
6. Poll the returned job through `GET /v1/jobs/{job_id}`.
7. Run the governed quality gate with `POST /v1/engineering/workspaces/validate`.
8. Run the production-readiness gate with `POST /v1/engineering/workspaces/readiness`.

## Current quality gate

The first gate intentionally supports a narrow, safe execution policy:

- Python projects: pytest and Ruff are required when detected.
- mypy is advisory when a `src/` tree is present.
- Node projects are recognized but package scripts are not executed yet.
- Unsupported stacks receive a contract-only result instead of a false "passed" claim.
- Command output is bounded before being persisted as job evidence.

This is deliberate. Package-manager scripts can execute arbitrary shell commands, so broader full-stack execution will be introduced behind a separate command-policy and sandbox boundary.

## Production architecture requirement

Repository workspaces are local worker storage, not durable application storage. The API is intentionally stateless with respect to the workspace filesystem. A production worker must run on compute with a lifecycle appropriate for disposable execution workspaces, while durable metadata remains in PostgreSQL and generated artifacts should move to object storage as the artifact pipeline is introduced.

The public Vercel API deployment is therefore the control plane, not the place to assume a persistent local filesystem. Vercel's current guidance recommends external backing services for state that must outlive a serverless instance.

## Next missions

- **102:** repository worktree + safe file mutation
- **103:** diff, commit and branch controller
- **104:** broader multi-language command policy
- **105:** agent planning and bounded task execution
- **106:** CI/build orchestration
- **107:** PR creation and review evidence
- **108:** deployment adapters
- **109:** production readiness and release gates
