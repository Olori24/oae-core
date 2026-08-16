# OAE SaaS API

The SaaS control plane exposes a tenant-scoped API around OAE and is ready for a controlled 20-developer beta.

## Local setup

```bash
cp .env.example .env
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn oae.api.app:app --reload
```

Open `http://127.0.0.1:8000/docs` for the generated OpenAPI UI.

## Create the 20-developer beta cohort

With the API running:

```bash
python scripts/create_beta_cohort.py
```

The utility creates `Developer 01` through `Developer 20` with isolated tenants and prints each tenant ID and one-time API key. Store the output securely. API keys are not recoverable because only their HMAC digests are stored.

## Run an authenticated job

The following smoke test creates a dedicated tenant, extracts its API key, queues a real repository analysis, extracts the returned job ID, and retrieves the job:

```bash
TENANT_JSON=$(curl -sS -X POST http://127.0.0.1:8000/v1/tenants \
  -H 'Content-Type: application/json' \
  -d '{"name":"CLI Smoke Test"}')

OAE_API_KEY=$(python -c 'import json,sys; print(json.load(sys.stdin)["api_key"])' <<< "$TENANT_JSON")

JOB_JSON=$(curl -sS -X POST http://127.0.0.1:8000/v1/jobs \
  -H "Authorization: Bearer $OAE_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"operation":"analyze","payload":{"repository_url":"https://github.com/Olori24/oae-core"}}')

JOB_ID=$(python -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<< "$JOB_JSON")

curl -sS "http://127.0.0.1:8000/v1/jobs/$JOB_ID" \
  -H "Authorization: Bearer $OAE_API_KEY"
```

The `analyze` operation is read-only and accepts public GitHub HTTPS repository URLs.

## Beta test checklist

Each developer should validate:

1. Authentication with their dedicated tenant key.
2. Public repository analysis.
3. Job polling and terminal states.
4. Analysis of repositories containing Python source and tests.
5. Rejection of invalid credentials.
6. Tenant isolation between developers.
7. Useful error messages for invalid operations or payloads.
8. Response latency and job execution reliability.

Shared credentials should not be used during the beta because tenant isolation is a core part of the test.

## API surface

| Endpoint | Purpose |
|---|---|
| `GET /` | Service status and API documentation path |
| `GET /health` | Health check |
| `POST /v1/tenants` | Create an isolated tenant and issue its API key |
| `GET /v1/me` | Return the authenticated tenant |
| `POST /v1/jobs` | Queue an engineering job |
| `GET /v1/jobs` | List the authenticated tenant's recent jobs |
| `GET /v1/jobs/{id}` | Retrieve one tenant-scoped job |
| `GET /docs` | Interactive OpenAPI documentation |

## Production configuration

Production must use:

- `APP_ENV=production`
- A strong random `API_KEY_PEPPER`
- A production database URL
- Exact production `ALLOWED_HOSTS`
- Exact production `CORS_ORIGINS`
- HTTPS termination
- Persistent storage
- External monitoring and logs

The application rejects the development API-key pepper when `APP_ENV=production`.

The current SQLite backend and in-process background task runner are suitable for a controlled beta and a single-instance deployment. Horizontal production scaling requires PostgreSQL and a durable queue/worker service.

## Deployment

The repository includes a production-oriented `Dockerfile` and `docker-compose.yml`. The environment file contains working local values so a developer can start the beta without editing template domains or placeholder secrets.
