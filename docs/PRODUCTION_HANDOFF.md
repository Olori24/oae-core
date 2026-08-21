# OAE Production Handoff

## Purpose and operating boundary

This guide is the operator handoff for moving OAE from a validated repository into a real deployment environment. It does **not** ask an operator to activate production traffic from a laptop or the Manus frontend. The React control plane remains managed at its existing HTTPS address; the Python API, PostgreSQL database, durable worker, outbox relay, and Caddy gateway must run together on an isolated persistent host.

> **Sequence rule:** First prove public DNS and Caddy reachability with the disposable staging ACME transaction. Only after that result is recorded should a production domain, production certificate, or durable feature flag be considered.

## Required decisions before an operator begins

| Decision | Required value | Why it matters |
|---|---|---|
| Deployment host | Persistent Linux host with Docker Engine and Docker Compose | OAE needs PostgreSQL, a durable worker, an outbox relay, and Caddy; the sandbox is not a production runtime. |
| API hostname | A dedicated hostname such as `api.example.com` | The frontend uses this as its explicit live API URL. |
| Frontend origin | The exact deployed frontend origin | It must be present in the API CORS allowlist. |
| Secret authority | A secret manager or protected host environment | Database passwords, API key pepper, and production secrets must never enter Git or the browser. |
| ACME contact | A monitored email address | Caddy uses `CADDY_EMAIL` for ACME account registration and certificate notices. |

## Stage A — disposable TLS proof

Use a disposable hostname such as `staging-api.example.com`, point DNS to the deployment host, and open TCP ports **80** and **443** through both the provider and host firewalls. Copy `.env.staging.example` to `.env.production` only on the isolated host, replace the example values with staging-only values, and keep both durable feature flags disabled.

Run the exact staging procedure in [Caddy TLS dry run](CADDY_TLS_DRY_RUN.md). Its success criterion is a Caddy log entry confirming a certificate from the **Let’s Encrypt staging** directory, plus an external `curl -vkI` response from `https://${API_DOMAIN}/health`. The `-k` switch is expected because staging certificates are intentionally untrusted by browsers.

Stop immediately if DNS does not point to the host, port 80 or 443 is unavailable, gateway logs show an ACME challenge failure, or a production secret appears in the staging environment file. Resolve that boundary first; do not switch to the production issuer to work around a failed staging challenge.

## Stage B — protected production activation

After the staging result is successful, create a fresh production environment file from `.env.production.example`. Use generated production passwords and a unique `API_KEY_PEPPER`; never reuse the staging database or staging secrets. Set `API_DOMAIN`, `CADDY_EMAIL`, the exact `CORS_ORIGINS` frontend origin, and PostgreSQL settings.

Run these commands from the checked-out, reviewed OAE release on the deployment host:

```bash
cp .env.production.example .env.production
chmod 600 .env.production
# Populate .env.production through the protected host or secret-manager workflow.

docker compose -f docker-compose.production.yml --env-file .env.production build
docker compose -f docker-compose.production.yml --env-file .env.production up -d db
docker compose -f docker-compose.production.yml --env-file .env.production run --rm migrate
docker compose -f docker-compose.production.yml --env-file .env.production up -d api worker relay gateway
docker compose -f docker-compose.production.yml --env-file .env.production ps
```

The API deliberately has no public host binding on port `8000`; only Caddy publishes ports `80` and `443`. Caddy must remain the HTTPS edge because its gateway configuration keeps SSE proxy buffering disabled.

## Stage C — activation evidence

Do not enable `DURABLE_JOBS_ENABLED=true` or `REALTIME_EVENTS_ENABLED=true` until the migration completed successfully and the worker and relay are healthy. The following evidence should be collected before inviting any live frontend user:

| Check | Expected result | Command or observation |
|---|---|---|
| Database | Healthy PostgreSQL service | `docker compose ... ps` shows `db` healthy |
| API | HTTPS health response through Caddy | `curl -fsS https://${API_DOMAIN}/health` |
| Certificate | Browser-trusted production certificate | `openssl s_client -connect ${API_DOMAIN}:443 -servername ${API_DOMAIN}` |
| Worker | Worker started with a unique runtime identity | `docker compose ... logs worker` |
| Relay | Relay is polling or waking for outbox work | `docker compose ... logs relay` |
| SSE | Authenticated stream returns headers and heartbeat/event data | use a tenant key against `/v1/events` |
| Browser | Frontend can provision or connect a tenant without CORS errors | OAE Settings → Connection & Security |

Run one low-risk tenant operation after the flags are enabled. Verify the job state, durable event delivery, and browser-side live stream independently. The client must show **LIVE** only when it has connected to the API; sample fixtures remain explicitly labeled **SAMPLE** or **SIMULATED**.

## Safe rollback

If the runtime is unhealthy, first stop accepting new work by setting `DURABLE_JOBS_ENABLED=false` and `REALTIME_EVENTS_ENABLED=false`, then restart the API, worker, and relay with the protected environment file. Preserve database volumes and gateway certificate volumes. Do not delete PostgreSQL data or Caddy state as part of a first-response rollback.

Use the [event-delivery runbook](REALTIME_EVENT_DELIVERY_RUNBOOK.md) for relay or worker diagnosis. For an unrecoverable release defect, return to the previously reviewed application image or Git revision, rerun the migration tool only when the migration plan explicitly supports it, and repeat the health, worker, relay, and authenticated SSE checks before reopening live access.

## What the August 27 reminder covers

The scheduled August 27 session is intentionally limited to the **Stage A staging ACME proof**. It does not authorize a production launch, a domain purchase, an infrastructure charge, or a secret change. The operator should return with the staging certificate evidence, the public hostname used, and any Caddy log error if the check fails.
