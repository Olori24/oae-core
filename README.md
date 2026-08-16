# OAE — Open Autonomous Engineer

### Autonomous Engineering Operating System + SaaS

> Analyze • Plan • Build • Verify • Improve

![Version](https://img.shields.io/badge/version-v0.6.0-blue)
![Tests](https://img.shields.io/badge/tests-773%20local%20baseline-brightgreen)
![Python](https://img.shields.io/badge/python-3.14-blue)
![Status](https://img.shields.io/badge/status-SaaS%20beta-orange)
![Architecture](https://img.shields.io/badge/architecture-modular-success)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

OAE is an autonomous engineering platform that analyzes software repositories, identifies engineering work, executes controlled engineering operations, verifies results, and keeps humans responsible for sensitive decisions.

The repository now includes a multi-tenant SaaS control plane and a browser onboarding experience for controlled developer testing.

---

## SaaS Beta

OAE is prepared for a controlled beta with **20 developers**.

Each developer operates through a tenant-scoped API key. Jobs are isolated by tenant, SaaS execution is restricted to an explicit operation allowlist, and repository writes remain protected by OAE's permission and human-approval security model.

### Beta capabilities

- Browser landing page and developer onboarding
- API-key login and tenant identity
- Multi-tenant API authentication
- Tenant-scoped job history
- Asynchronous job execution
- Repository analysis for public GitHub HTTPS repositories
- Analyze, review, and verify operations
- Per-tenant 30-day job quota
- Request IDs and security headers
- Production secret validation
- Docker deployment foundation
- OpenAPI documentation
- CI compile and test gates

### Test baseline

The latest local verification baseline is **773 passing tests**. CI also verifies compilation and the complete test suite.

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/Olori24/oae-core.git
cd oae-core
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure local development

```bash
cp .env.example .env
```

The repository ships with working local-development values. Do not use those development values for production.

### 3. Start the application

```bash
uvicorn oae.api.app:app --reload
```

Open:

- `http://127.0.0.1:8000/` — browser onboarding and dashboard
- `http://127.0.0.1:8000/health` — health check
- `http://127.0.0.1:8000/docs` — interactive API documentation

---

## Browser Onboarding

The root page is now the beta entry point.

A new developer can:

1. Create a workspace.
2. Receive a one-time API key.
3. Continue directly into the workspace dashboard.
4. Log back in later with the API key.
5. Submit a public GitHub repository for analysis.
6. Poll the job until completion.
7. Inspect the returned engineering result.
8. Log out and authenticate again.

The browser stores the API key only in session storage. OAE stores only an HMAC digest of the key server-side.

For the initial 20-person cohort, do not share one API key across developers.

---

## Developer Beta Onboarding

The initial test group is 20 developers. Give each developer a separate tenant rather than sharing one API key.

### Create all 20 tester tenants

With the API running, execute:

```bash
python scripts/create_beta_cohort.py
```

The script creates `Developer 01` through `Developer 20` and prints a one-time CSV-style list containing each tenant ID and API key. Store that output securely. API keys cannot be recovered after creation because OAE stores only their HMAC digests.

### Recommended 20-developer test

Each developer should test the same core workflow first:

1. Create or receive a dedicated tenant API key.
2. Run a public GitHub repository analysis.
3. Poll the job until it reaches a terminal status.
4. Repeat with a repository containing Python source and tests.
5. Test invalid authentication and confirm it is rejected.
6. Confirm one developer cannot read another developer's job.
7. Report execution errors, unexpected results, latency, and API usability issues.

---

## API Surface

| Endpoint | Purpose |
|---|---|
| `GET /` | Browser onboarding and developer dashboard |
| `GET /health` | Health check |
| `POST /v1/tenants` | Create an isolated tenant and issue its API key |
| `GET /v1/me` | Return the authenticated tenant |
| `POST /v1/jobs` | Queue an engineering job |
| `GET /v1/jobs` | List the authenticated tenant's recent jobs |
| `GET /v1/jobs/{id}` | Retrieve one tenant-scoped job |
| `GET /docs` | Interactive OpenAPI documentation |

---

## Security Model

OAE is designed for controlled autonomous engineering rather than unrestricted code execution.

### Protected by default

- Repository writes require permission and human approval.
- Shell execution is disabled by default.
- File deletion is disabled by default.
- Force-push is disabled by default.
- Unknown operations are rejected by the SaaS execution layer.
- API keys are not stored in plaintext.
- Production deployments require a non-default API key pepper.
- Tenant data and job access are scoped to the authenticated tenant.

Do not disable these controls simply to make a workflow convenient. They are part of OAE's engineering contract.

---

## Current Architecture

```text
Developer
   |
   v
Browser Onboarding
   |
   v
FastAPI SaaS Control Plane
   |
   +--> Tenant Authentication
   +--> Quota Enforcement
   +--> Job Store
   +--> Operation Allowlist
   |
   v
Autonomous Engineering Core
   |
   +--> Repository Intelligence
   +--> Planning
   +--> Engineering Actions
   +--> Verification
   +--> Security Kernel
   |
   v
Engineering Result
```

The SaaS layer is a controlled entry point around the existing OAE engineering core; it does not replace the autonomous engineering architecture.

---

## Core Capabilities

### Repository Intelligence

- Repository Scanner
- Repository Profiler
- Repository Sandbox
- Workspace Manager
- Repository Recovery Engine
- Repository Knowledge Graph
- Dependency and dead-code analysis

### Engineering Intelligence

- Engineering Review Engine
- Capability Discovery Engine
- Semantic Repository Analyzer
- Capability Planner
- Dependency Resolver
- Engineering Analysis Engine

### Autonomous Engineering

- Bootstrap Engine
- Application Scaffold Generator
- Mission Queue
- Scheduler
- Verification Engine
- Rollback infrastructure
- Repository execution engine

### Multi-Agent System

- Agent Runtime
- Agent Registry
- Agent Message Bus
- Shared Agent Memory
- Engineering action executor

### SaaS Control Plane

- FastAPI API
- Browser onboarding
- Tenant authentication
- Tenant-scoped jobs
- Background job execution
- Public GitHub repository analysis
- Usage quotas
- Security middleware
- Docker deployment foundation

---

## Production Deployment

For production, configure:

- `APP_ENV=production`
- A strong random `API_KEY_PEPPER`
- A production database URL
- Exact production `ALLOWED_HOSTS`
- Exact production `CORS_ORIGINS`
- HTTPS termination
- Persistent storage
- External monitoring and logs

The included Dockerfile and `docker-compose.yml` provide a single-instance deployment foundation with persistent Docker volume storage.

**Production infrastructure caveat:** the current implementation uses SQLite and in-process background tasks. That is appropriate for a controlled single-instance beta, not horizontal production scaling. PostgreSQL plus a durable worker queue should be used before multi-instance production traffic.

See [`docs/SAAS.md`](docs/SAAS.md) for API and deployment details.

---

## Engineering Principles

- Security First
- Human Approval
- Verification Required
- Repository Safety
- Modular Architecture
- Test Before Integration
- Continuous Engineering
- Tenant Isolation

Quality comes before autonomy.

---

## Roadmap

### SaaS Beta

- 20-developer controlled testing
- API reliability testing
- Tenant isolation validation
- Job execution validation
- Security testing
- Developer feedback collection

### Production Platform

- PostgreSQL persistence
- Durable job queue and workers
- GitHub App / OAuth for private repositories
- Billing and plan enforcement
- Production observability
- Production domain and deployment

### OAE v1.0

Autonomous engineering teams capable of understanding, improving, testing, documenting, and governing software repositories with minimal human intervention while keeping humans responsible for strategic decisions and sensitive approvals.

---

## License

MIT License
