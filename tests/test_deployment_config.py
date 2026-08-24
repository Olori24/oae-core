from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_production_compose_exposes_only_https_gateway_ports():
    compose = (ROOT / "docker-compose.production.yml").read_text(encoding="utf-8")

    for service in ("db:", "api:", "worker:", "relay:", "migrate:", "gateway:"):
        assert f"  {service}" in compose
    assert '      - "80:80"' in compose
    assert '      - "443:443"' in compose
    assert '      - "8000:8000"' not in compose
    assert "    expose:\n      - \"8000\"" in compose
    assert "condition: service_healthy" in compose
    assert "oae-postgres:/var/lib/postgresql/data" in compose
    assert "oae-data:/app/data" in compose


def test_production_environment_template_enables_durable_event_delivery_without_secrets():
    environment = (ROOT / ".env.production.example").read_text(encoding="utf-8")

    required = (
        "API_DOMAIN=api.example.com",
        "POSTGRES_DB=oae",
        "POSTGRES_USER=oae",
        "POSTGRES_PASSWORD=",
        "DATABASE_URL=postgresql://oae:${POSTGRES_PASSWORD}@db:5432/oae",
        "API_KEY_PEPPER=",
        "DURABLE_JOBS_ENABLED=true",
        "REALTIME_EVENTS_ENABLED=true",
        "WORKSPACE_ROOT=/app/data/oae-workspaces",
        "SSE_MAX_CONNECTION_SECONDS=300",
    )
    for setting in required:
        assert setting in environment


def test_staging_environment_template_keeps_governed_worker_enforcement_off_initially():
    environment = (ROOT / ".env.staging.example").read_text(encoding="utf-8")

    required = (
        "APP_ENV=staging",
        "ALLOWED_HOSTS=[\"staging-api.example.com\"]",
        "CORS_ORIGINS=[\"https://oaeengineer-3nncbrhe.manus.space\"]",
        "WORKER_AUTHORIZATION_ENFORCEMENT_ENABLED=false",
        "API_CONTROL_RATE_LIMIT_PER_MINUTE=60",
    )
    for setting in required:
        assert setting in environment


def test_caddy_keeps_sse_proxy_flush_unbuffered():
    caddyfile = (ROOT / "Caddyfile").read_text(encoding="utf-8")

    assert "email {$CADDY_EMAIL}" in caddyfile
    assert "{$API_DOMAIN}" in caddyfile
    assert "reverse_proxy api:8000" in caddyfile
    assert "flush_interval -1" in caddyfile


def test_staging_caddyfile_uses_letsencrypt_staging_and_preserves_gateway_policy():
    caddyfile = (ROOT / "Caddyfile.staging").read_text(encoding="utf-8")
    compose = (ROOT / "docker-compose.staging.yml").read_text(encoding="utf-8")

    assert "email {$CADDY_EMAIL}" in caddyfile
    assert "acme_ca https://acme-staging-v02.api.letsencrypt.org/directory" in caddyfile
    assert "{$API_DOMAIN}" in caddyfile
    assert "reverse_proxy api:8000" in caddyfile
    assert "flush_interval -1" in caddyfile
    assert "./Caddyfile.staging:/etc/caddy/Caddyfile:ro" in compose
