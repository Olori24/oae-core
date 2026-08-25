# Production Template Placeholder Baseline

**Assessment date:** 25 August 2026  
**Published preflight revision:** `7b62dc84cb915fe18c664d395c0c3b328bbdc32b`  
**Input:** `.env.production.example` only

## Result

The environment-placeholder preflight returned **FAIL** with **29 passing variables and 7 unresolved variables**. This is the expected baseline for a committed production template: the template should declare its full configuration contract but must not contain production secrets, a production domain, or production contact information.

| Category | Unresolved names | Reason class |
|---|---|---|
| Network | `ALLOWED_HOSTS`, `API_DOMAIN`, `CADDY_EMAIL` | Template placeholder values must be replaced on the host. |
| Sensitive | `API_KEY_PEPPER`, `POSTGRES_PASSWORD`, `SECRET_KEY` | Required host-managed secrets are intentionally empty. |
| Database | `DATABASE_URL` | It correctly depends on the unresolved `POSTGRES_PASSWORD` variable. |

The preflight reported variable names, categories, and readiness reasons only. A separate value-redaction check passed, confirming that the generated report did not render representative template configuration values.

## Contract correction

The initial baseline also detected that `WORKER_AUTHORIZATION_ENFORCEMENT_ENABLED` was required by the staging preflight contract but not declared in the production template. The template now explicitly sets it to `false`, preserving OAE’s deliberate activation hold until the separate-principal PostgreSQL staging procedure has passed. The updated deployment and preflight regression suite passed **14 tests**.

## Interpretation

This is a **PASS for template design** and a **FAIL for direct deployment**, as intended. A host operator must replace the seven named values through approved secret management, then re-run the script against the actual protected host environment file. A zero exit status is necessary before the host-mode staging preflight, but it does not validate secret strength, DNS, Docker, Caddy, PostgreSQL, migrations, worker health, TLS, or governed execution.

## References

[1] [Environment Placeholder Preflight](ENVIRONMENT_PLACEHOLDER_PREFLIGHT.md)

[2] [Staging Readiness Simulation](STAGING_READINESS_SIMULATION_2026_08_25.md)
