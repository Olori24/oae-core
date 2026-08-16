# OAE — Open Autonomous Engineer

### Autonomous Engineering Operating System + SaaS API

> Analyze • Plan • Build • Verify • Improve

![Version](https://img.shields.io/badge/version-v0.6.0-blue)
![Tests](https://img.shields.io/badge/tests-773%20passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.14-blue)
![Status](https://img.shields.io/badge/status-SaaS%20beta-orange)
![Architecture](https://img.shields.io/badge/architecture-modular-success)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

OAE is an autonomous engineering platform that analyzes software repositories, identifies engineering work, executes controlled engineering operations, verifies results, and keeps humans responsible for sensitive decisions.

The project now includes a deployable multi-tenant SaaS control plane for developer testing.

---

## SaaS Beta

OAE is ready for a controlled beta with **20 developers**.

Each developer operates through a tenant-scoped API key. Jobs are isolated by tenant, execution is restricted to an explicit operation allowlist, and repository writes remain protected by OAE's permission and human-approval security model.

### Beta capabilities

- Multi-tenant API authentication
- Tenant-scoped job history
- Asynchronous job execution
- Repository analysis for public GitHub HTTPS repositories
- Analyze, review, and verify operations
- Per-tenant 30-day job quota
- Request IDs and security headers
- Production secret validation
- Docker deployment
- OpenAPI documentation
- CI compile and test gates

### Current test baseline

**773 automated tests passing** in the latest local verification run.

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

The repository now ships with working local-development values. Do not use those development values for a production deployment.

### 3. Start the API

```bash
uvicorn oae.api.app:app --reload
```

The API will be available at:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

---

## Developer Beta Onboarding

The intended first test group is 20 developers. Give each developer a separate tenant rather than sharing one API key.

### Create a tester tenant

```bash
curl -X POST http://127.0.0.1:8000/v1/tenants \
  -H 'Content-Type: application/json' \
  -d '{"name":"Developer 01"}'
```

The response contains the developer's API key. Store it securely because OAE stores only its HMAC digest and cannot recover the original key.

Repeat with `Developer 02` through `Developer 20` for the initial beta cohort.

### Run the first analysis

Replace `YOUR_API_KEY` with the key returned when the tenant was created:

```bash
curl -X POST http://127.0.0.1:8000/v1/jobs \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"operation":"analyze","payload":{"repository_url":"https://github.com/Olori24/oae-core"}}'
```

Poll the returned job ID:

```bash
curl http://127.0.0.1:8000/v1/jobs/JOB_ID \
  -H 'Authorization: Bearer YOUR_API_KEY'
```

For the complete API surface, open `/docs` after starting the service.

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
- Production deployments must provide a non-default API key pepper.
- Tenant data and job access are scoped to the authenticated tenant.

Do not disable these controls simply to make a workflow convenient. They are part of OAE's core engineering contract.

---

## Current Architecture

```text
Developer
   |
   v
FastAPI SaaS Control Plane
   |
   +--> Tenant Authentication
   |
   +--> Quota Enforcement
   |
   +--> Job Store
   |
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
- Tenant authentication
- Tenant-scoped jobs
- Background job execution
- Public GitHub repository analysis
- Usage quotas
- Security middleware
- Docker deployment

---

## Engineering Workflow

```text
Repository
   ↓
Repository Analysis
   ↓
Engineering Review
   ↓
Capability Discovery
   ↓
Planning
   ↓
Security / Human Approval
   ↓
Implementation
   ↓
Verification
   ↓
Repository Re-analysis
   ↓
Engineering Health Improvement
```

---

## Production Deployment

For a production deployment, configure:

- `APP_ENV=production`
- A strong random `API_KEY_PEPPER`
- A production database URL
- Exact production `ALLOWED_HOSTS`
- Exact production `CORS_ORIGINS`
- HTTPS termination
- Persistent storage
- External monitoring and logs

The included Dockerfile and `docker-compose.yml` provide the deployment foundation. The current SQLite storage and in-process background execution are suitable for controlled beta testing and a single-instance deployment. A horizontally scaled production service should move persistence to PostgreSQL and jobs to a durable worker queue.

See [`docs/SAAS.md`](docs/SAAS.md) for the API and deployment details.

---

## Benchmark: Opportunity Radar Africa

OAE has been validated against a real software repository through an autonomous engineering cycle:

```text
Repository Analysis
↓
Engineering Review
↓
Engineering Recommendations
↓
Human Approval
↓
Implementation
↓
Verification
↓
Repository Re-analysis
```

The benchmark cycle improved the repository engineering health from **91 to 94** and verified structured logging as the first completed recommendation.

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
- Public dashboard and developer console
- Production domain and deployment

### OAE v1.0

Autonomous engineering teams capable of understanding, improving, testing, documenting, and governing software repositories with minimal human intervention while keeping humans responsible for strategic decisions and sensitive approvals.

---

## Contributing

Every contribution must:

- Include automated tests
- Preserve repository safety
- Pass verification
- Respect tenant isolation
- Follow engineering governance

Pull requests are expected to pass the CI compile and test gates before integration.

---

## License

MIT License
