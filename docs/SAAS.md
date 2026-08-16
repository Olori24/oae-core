# OAE SaaS API

The SaaS control plane exposes a tenant-scoped API around OAE.

## Local

```bash
cp .env.example .env
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn oae.api.app:app --reload
```

Open `/docs` for the generated OpenAPI UI.

## Create a tenant

```bash
curl -X POST http://localhost:8000/v1/tenants \
  -H 'Content-Type: application/json' \
  -d '{"name":"Acme"}'
```

Store the returned API key securely. It is not recoverable from the database because only its HMAC digest is stored.

## Run a job

```bash
curl -X POST http://localhost:8000/v1/jobs \
  -H 'Authorization: Bearer oae_...' \
  -H 'Content-Type: application/json' \
  -d '{"operation":"analyze","payload":{"repository_url":"https://github.com/Olori24/oae-core"}}'
```

Poll the returned job ID with `GET /v1/jobs/{id}`. The analyze operation is read-only and accepts public GitHub HTTPS repository URLs.

## Production

Set a strong `API_KEY_PEPPER`, a real `DATABASE_URL`, `ALLOWED_HOSTS`, and `CORS_ORIGINS`. The application rejects the default API-key secret when `APP_ENV=production`.

The current SQLite backend is suitable for a single-instance deployment and local development. For horizontal scaling, the persistence layer should be switched to PostgreSQL and the in-process background task runner should be replaced with a durable queue/worker service.
