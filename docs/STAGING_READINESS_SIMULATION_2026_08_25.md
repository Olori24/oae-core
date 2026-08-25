# OAE Staging Readiness Simulation

**Assessment date:** 25 August 2026  
**Published revision assessed:** `358d05b2a1ab55aa4624598853cca7a9bafda00d`  
**Mode:** Non-destructive sandbox simulation

> This simulation validates committed configuration and host-preflight behavior. It did not start containers, bind ports, request a certificate, contact a database, pull a model, or produce worker, relay, SSE, or telemetry evidence.

## Result summary

| Check | Result | Evidence and interpretation |
|---|---|---|
| Deployment asset inventory | **PASS** | Production, staging, and private-model Compose overlays; Caddy files; environment templates; preflight; and telemetry collector are present. |
| Deployment topology regression | **PASS** | 15 deployment, staging-validation, and private-model-overlay tests passed. |
| Private API exposure policy | **PASS** | Static tests confirm the production topology exposes only Caddy ports 80 and 443 while retaining API port 8000 as an internal service exposure. |
| Caddy staging policy | **PASS** | Static tests confirm configurable email and domain values, the Let’s Encrypt staging CA, reverse proxy to `api:8000`, and `flush_interval -1` for SSE. |
| Bootstrap feature-flag posture | **PASS** | The staging template retains `WORKER_AUTHORIZATION_ENFORCEMENT_ENABLED=false`, preserving the governed-execution activation hold. |
| Private model overlay posture | **PASS** | Static tests confirm the Ollama overlay has no published `11434` host port and isolates the Qwen3 8B pull profile. |
| Template environment contract | **PARTIAL** | Required keys and bootstrap flags are present. The expected template placeholders for `API_DOMAIN`, `CADDY_EMAIL`, `POSTGRES_PASSWORD`, and `API_KEY_PEPPER` remain intentionally unset. |
| Compose runtime validation | **UNKNOWN** | Docker and Docker Compose are unavailable in this sandbox, so `docker compose config --quiet` could not run. |
| Caddy binary validation | **UNKNOWN** | No local Caddy binary is available in the sandbox for a `caddy validate` check. |
| Public DNS, firewall, and ACME | **UNKNOWN** | The template does not carry a real hostname, and the sandbox has no staging network boundary. |
| PostgreSQL, migration, worker, relay, and SSE behavior | **UNKNOWN** | No service stack was started. No database, durable event, or connection-capacity evidence was generated. |
| Governed build authorization | **UNKNOWN** | The feature remains disabled in bootstrap configuration and has not been exercised against PostgreSQL staging. |

## Preflight simulation

The committed preflight was executed with `.env.staging.example`, `--execution-context sandbox`, and the published revision as the expected SHA. It verified the readable template, required environment-key names, Compose-file presence, bootstrap flag posture, private API-port configuration, and revision match. It correctly reported unavailable Docker and public DNS as `UNKNOWN` rather than passing them.

The command returned a non-zero status because the example environment has intentionally unresolved values for the API domain, Caddy email, PostgreSQL password, and API-key pepper. That is the correct result for a template file and must not be treated as a deployment failure.

```bash
python3 scripts/staging_preflight.py \
  --env-file .env.staging.example \
  --stage bootstrap \
  --execution-context sandbox \
  --expected-revision 358d05b2a1ab55aa4624598853cca7a9bafda00d
```

## What this simulation proves

The committed source includes a topology with PostgreSQL, API, worker, relay, migration job, and Caddy gateway; preserves the private API-port rule; encodes staging ACME policy; keeps initial governed worker enforcement inactive; and protects the private model overlay from public port exposure. The repository’s regression tests protect these configuration expectations. [1] [2]

It does not prove that Docker can build the images, that Compose resolves all runtime interpolation, that Caddy obtains a certificate, that a firewall exposes only the intended ports, that PostgreSQL migrates correctly, or that any governed-execution control works on a host.

## Connected-host handoff

Use an isolated staging server with Docker Compose, PostgreSQL storage, a staging DNS name, and inbound TCP 80 and 443. Populate the host environment file through approved secret management only. Do not paste passwords, API keys, private keys, or the full environment file into chat.

On that host, run the preflight in `host` mode using the actual staged revision. Resolve any `FAIL` result before continuing. Then run Compose configuration validation, start the database, apply migrations, start the API, worker, relay, and gateway, and retain redacted service-state evidence. Use the staging ACME procedure before any production issuer. Finally, follow the real-host governed-execution procedure to validate role separation, self-approval denial, approval, revocation, worker enforcement, pagination, rate limiting, outbox delivery, and authenticated SSE. [3] [4]

## Final classification

The repository is **configuration-validated for staging handoff**. It is not **container-runtime validated**, **network validated**, or **host validated** in this sandbox. Those remain explicit release gates.

## References

[1] [OAE deployment configuration tests](../tests/test_deployment_config.py)

[2] [OAE README deployment and governed-execution guidance](../README.md)

[3] [Caddy TLS staging dry-run procedure](CADDY_TLS_DRY_RUN.md)

[4] [Real-host Phase 2 governed-execution validation](REAL_HOST_PHASE_2_VALIDATION.md)
