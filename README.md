# OAE — Open Autonomous Engineer

### Autonomous Engineering Operating System + SaaS

> Analyze • Plan • Build • Verify • Improve

![Version](https://img.shields.io/badge/version-v0.6.0-blue)
![Tests](https://img.shields.io/badge/tests-773%20local%20baseline-brightgreen)
![Python](https://img.shields.io/badge/python-3.14-blue)
![Status](https://img.shields.io/badge/status-SaaS%20beta-orange)
![Architecture](https://img.shields.io/badge/architecture-modular-success)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

OAE is an autonomous engineering platform for understanding software repositories, identifying engineering work, executing controlled engineering operations, verifying results, and keeping humans responsible for sensitive decisions.

The repository includes a multi-tenant SaaS control plane and a cinematic browser workspace designed for controlled developer testing.

---

## SaaS Beta

OAE is prepared for a controlled **20-developer beta cohort**.

Each developer gets an isolated tenant and API key. Jobs are scoped to that tenant, SaaS operations are explicitly allowlisted, and sensitive repository writes remain protected by OAE's permission, policy, approval, and audit model.

### What a developer can do now

- Open the cinematic OAE landing page and understand the product without a manual walkthrough
- Create an isolated developer workspace
- Receive a one-time API key and securely continue into the workspace
- Sign back in with the API key
- Submit a public GitHub HTTPS repository for analysis
- Track queued/running/completed/failed jobs
- Inspect tenant-scoped mission history
- See repositories discovered from previous analysis jobs
- Explore OAE's engineering capabilities and security posture
- Use the interactive OpenAPI documentation at `/docs`
- Verify service health at `/health`

### Supported SaaS operations

- `analyze` — public GitHub repository analysis
- `review` — structured review of supplied findings
- `verify` — explicit verification of supplied checks/results

The SaaS layer intentionally does **not** expose unrestricted shell execution or arbitrary repository writes to internet users.

---

## Developer onboarding

### Browser flow

1. Open the OAE production URL.
2. Select **Launch workspace**.
3. Enter a workspace/team name.
4. Save the one-time API key.
5. Enter the workspace.
6. Sign out and sign back in to verify persistence.
7. Submit a public GitHub repository through the job API or an enabled client.
8. Watch the mission move through the engineering pipeline and inspect the result.

For the initial cohort, every developer should have a separate tenant. Do not share one API key across the team.

### Create all 20 beta tenants

With the API running, execute:

```bash
python scripts/create_beta_cohort.py
```

The script creates `Developer 01` through `Developer 20` and prints a one-time CSV-style list containing each tenant ID and API key. Store that output securely. API keys cannot be recovered after creation because OAE stores only their salted PBKDF2 hashes.

### Recommended beta test

Ask each developer to:

1. Authenticate with their dedicated key.
2. Analyze a public GitHub repository.
3. Inspect the returned repository intelligence.
4. Repeat with a repository containing Python source and tests.
5. Try invalid authentication and confirm it is rejected.
6. Confirm another tenant's job cannot be accessed.
7. Record errors, latency, confusing UX, and unexpected analysis results.

---

## Product surface

The root browser experience is intentionally more than a static marketing page. It contains:

- Cinematic product introduction
- Workspace creation and API-key authentication
- Responsive Mission Control dashboard
- Tenant-scoped mission history
- Repository history
- Engineering pipeline visualization
- Agent capability map
- Repository intelligence overview
- Security posture view
- Workspace identity/settings view
- Mobile-responsive layout
- Loading, empty, success and error states

The dashboard surfaces the existing OAE architecture instead of pretending the SaaS has capabilities that the API does not expose.

---

## API Surface

| Endpoint | Purpose |
|---|---|
| `GET /` | Cinematic browser onboarding and Mission Control |
| `GET /health` | Health check and active database backend |
| `POST /v1/tenants` | Create an isolated tenant and issue its API key |
| `GET /v1/me` | Return the authenticated tenant |
| `POST /v1/jobs` | Queue an engineering job |
| `GET /v1/jobs` | List the authenticated tenant's recent jobs |
| `GET /v1/jobs/{id}` | Retrieve one tenant-scoped job |
| `GET /docs` | Interactive OpenAPI documentation |

---

## Security model

OAE is designed for controlled autonomous engineering rather than unrestricted code execution.

### Protected by default

- Repository writes require permission and human approval.
- Shell execution is disabled by default.
- File deletion is disabled by default.
- Force-push is disabled by default.
- Unknown SaaS operations are rejected by the job runner.
- API keys are not stored in plaintext.
- Production deployments require a non-default API key pepper.
- Tenant data and job access are scoped to the authenticated tenant.
- Request IDs and security headers are applied at the API boundary.

Do not disable these controls merely to make a workflow convenient. They are part of OAE's engineering contract.

---

## Architecture

```text
Developer
   |
   v
Cinematic Browser Workspace
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
   +--> Knowledge Graph
   +--> Planning
   +--> Engineering Actions
   +--> Verification
   +--> Security Kernel
   +--> Agent Registry + Message Bus
   +--> Shared Memory
   |
   v
Engineering Result
```

The SaaS layer is a controlled entry point around the existing engineering core. It does not replace the autonomous engineering architecture.

---

## Core capabilities

### Repository Intelligence

- Repository Scanner
- Repository Profiler
- Repository Sandbox
- Workspace Manager
- Repository Recovery Engine
- Repository Knowledge Graph
- Dependency analysis
- Dead-code detection
- Circular-dependency detection

### Engineering Intelligence

- Engineering Review Engine
- Capability Discovery Engine
- Semantic Repository Analyzer
- Capability Planner
- Dependency Resolver
- Engineering Analysis Engine
- Engineering Ledger

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
- Architect, Builder, Verifier, Security and DevOps-oriented capabilities

### SaaS Control Plane

- FastAPI API
- Cinematic browser onboarding
- Tenant authentication
- Tenant-scoped jobs
- Background job execution
- Public GitHub repository analysis
- Usage quotas
- Security middleware
- PostgreSQL-compatible production persistence
- SQLite local-development fallback

---

## Quick start

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

Local development falls back to SQLite when no database URL is supplied. Production must use PostgreSQL.

### 3. Start the application

```bash
uvicorn oae.api.app:app --reload
```

Open:

- `http://127.0.0.1:8000/` — browser workspace
- `http://127.0.0.1:8000/health` — health check
- `http://127.0.0.1:8000/docs` — API documentation

---

## Production deployment

OAE's serverless SaaS control plane now supports a persistent PostgreSQL database and automatically detects common Vercel/Neon connection variables. Configure one of these in the Vercel production environment:

- `DATABASE_URL` — preferred
- `POSTGRES_URL` — supported for Vercel/Neon integrations
- `POSTGRES_PRISMA_URL` — supported as a fallback
- `POSTGRES_URL_NON_POOLING` — supported as a fallback

Also configure:

- `APP_ENV=production`
- A strong random `API_KEY_PEPPER`
- Exact production `ALLOWED_HOSTS`
- Exact production `CORS_ORIGINS`
- HTTPS termination
- External monitoring and logs

The application creates its required tables and indexes automatically on first database access. The schema is portable across local SQLite and production PostgreSQL.

**Important:** do not run the production SaaS on Vercel's ephemeral filesystem. SQLite is intentionally retained only as a local-development fallback. A persistent PostgreSQL database is required for multi-developer testing because serverless instances may be replaced at any time.

The Vercel deployment explicitly exports `src.oae.api.app:app`, so FastAPI entrypoint detection is deterministic.

---

## Test baseline

The repository's previous local baseline is **773 passing tests**. The database adapter change preserves the existing SQLite test path while adding the production PostgreSQL dependency and portable SQL layer.

For every SaaS UI change, also validate the browser flow: page load → workspace creation/login → dashboard → job submission → result → sign-out → sign-in.

---

## Engineering principles

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

### Controlled Beta

- 20-developer testing
- API reliability testing
- Tenant isolation validation
- Job execution validation
- Security testing
- Developer feedback collection

### Scale-up

- Durable job queue and workers
- GitHub App / OAuth for private repositories
- Billing and plan enforcement
- Production observability
- Production domain and deployment

### OAE v1.0

Autonomous engineering teams capable of understanding, improving, testing, documenting and governing software repositories with minimal human intervention while keeping humans responsible for strategic decisions and sensitive approvals.

---

## License

MIT License
