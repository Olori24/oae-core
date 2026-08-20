# Durable Worker, Relay, and SSE Activation Runbook

## Purpose

This runbook activates OAE’s PostgreSQL-backed durable job workers, transactional outbox relay, and authenticated Server-Sent Events delivery. It is intentionally an **operator-controlled** deployment procedure. Do not turn on durable enqueue or realtime delivery against SQLite, without the tracked PostgreSQL migrations, or before a worker and relay have started successfully.

## Required Runtime Topology

The production compose file starts four long-lived services: `api`, `worker`, `relay`, and PostgreSQL. The migration job is deliberately a one-shot tool service. All services use the same production environment file, while API and workers share the persistent workspace volume.

| Service | Responsibility | Required before traffic |
|---|---|---|
| `db` | PostgreSQL durable authority for jobs, events, leases, and replay cursors | Healthy and backed up. |
| `migrate` | Applies `0001` through the newest tracked migration exactly once | Completed successfully. |
| `worker` | Claims, renews, retries, and finalizes leased jobs | At least one healthy instance. |
| `relay` | Projects transactional outbox rows and powers SSE replay | At least one healthy instance. |
| `api` | Authenticates requests and serves replay/SSE endpoints | Behind HTTPS with exact CORS and host configuration. |

## Production Environment

Create an uncommitted `.env.production` file owned by the deployment environment. Set unique secrets and do not reuse development values.

```dotenv
APP_ENV=production
POSTGRES_DB=oae
POSTGRES_USER=oae
POSTGRES_PASSWORD=<generated-database-password>
DATABASE_URL=postgresql://oae:<generated-database-password>@db:5432/oae
SECRET_KEY=<generated-application-secret>
API_KEY_PEPPER=<generated-api-key-pepper>
ALLOWED_HOSTS=["api.example.com"]
CORS_ORIGINS=["https://oaeengineer-3nncbrhe.manus.space"]
WORKSPACE_ROOT=/app/data/oae-workspaces
DURABLE_JOBS_ENABLED=true
REALTIME_EVENTS_ENABLED=true
```

Retain the documented lease, retry, relay, and SSE defaults unless capacity testing establishes a different safe value. The browser frontend must use the public HTTPS API URL, not the internal compose hostname.

## Activation Sequence

Build the images and start PostgreSQL first. Apply migrations as a one-shot job before starting the API, worker, or relay.

```bash
docker compose -f docker-compose.production.yml --env-file .env.production build
docker compose -f docker-compose.production.yml --env-file .env.production up -d db
docker compose -f docker-compose.production.yml --env-file .env.production run --rm migrate
docker compose -f docker-compose.production.yml --env-file .env.production up -d api worker relay
```

Confirm each process is healthy before allowing production job submissions.

```bash
docker compose -f docker-compose.production.yml --env-file .env.production ps
curl --fail https://api.example.com/health
docker compose -f docker-compose.production.yml --env-file .env.production logs --tail=100 worker relay
```

Create a tenant API key, submit one low-risk job, and verify that the worker claims it, the relay projects the resulting events, and an authenticated client receives `GET /v1/events` with a monotonic cursor. The frontend should then connect using the same tenant key and display **LIVE STREAM · CONNECTED**, never simulated wording.

## Rollback and Incident Controls

If workers or the relay are unhealthy, immediately set `DURABLE_JOBS_ENABLED=false` and `REALTIME_EVENTS_ENABLED=false`, then restart the API. Do not downgrade PostgreSQL migrations or delete outbox/replay rows during an incident. Preserve the database, relay logs, worker logs, and the oldest unpublished outbox age for investigation.

The existing REST job read endpoints remain available for recovery. The frontend’s snapshot endpoint handles expired replay cursors by rebuilding the visible state before reconnecting.
