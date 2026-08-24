from pathlib import Path

from scripts import collect_staging_telemetry, staging_preflight


def test_environment_checks_reject_missing_or_placeholder_governed_configuration():
    values = {
        "APP_ENV": "staging",
        "API_DOMAIN": "staging-api.example.com",
        "CADDY_EMAIL": "operator@example.com",
        "POSTGRES_DB": "oae",
        "POSTGRES_USER": "oae",
        "POSTGRES_PASSWORD": "replace-me",
        "DATABASE_URL": "postgresql://oae:${POSTGRES_PASSWORD}@db:5432/oae",
        "API_KEY_PEPPER": "replace-me",
        "ALLOWED_HOSTS": "[\"staging-api.example.com\"]",
        "CORS_ORIGINS": "[\"https://console.example.com\"]",
        "DURABLE_JOBS_ENABLED": "true",
        "REALTIME_EVENTS_ENABLED": "true",
        "WORKER_AUTHORIZATION_ENFORCEMENT_ENABLED": "false",
    }

    checks = {check.name: check for check in staging_preflight.environment_checks(values, "governed")}

    assert checks["environment_value_safety"].status == "FAIL"
    assert checks["feature_flag_stage"].status == "FAIL"
    assert "POSTGRES_PASSWORD" in checks["environment_value_safety"].detail
    assert "WORKER_AUTHORIZATION_ENFORCEMENT_ENABLED" in checks["feature_flag_stage"].detail


def test_preflight_does_not_report_secret_values(tmp_path: Path):
    env_file = tmp_path / ".env.production"
    env_file.write_text("API_KEY_PEPPER=top-secret-value\n", encoding="utf-8")

    parsed = staging_preflight.parse_env_file(env_file)
    rendered = staging_preflight.redact("API_KEY_PEPPER=top-secret-value\nBearer abc123")

    assert parsed["API_KEY_PEPPER"] == "top-secret-value"
    assert "top-secret-value" not in rendered
    assert "abc123" not in rendered


def test_api_port_privacy_check_accepts_internal_expose_and_rejects_host_binding(tmp_path: Path):
    internal = tmp_path / "internal.yml"
    internal.write_text('services:\n  api:\n    expose:\n      - "8000"\n  db:\n', encoding="utf-8")
    public = tmp_path / "public.yml"
    public.write_text('services:\n  api:\n    ports:\n      - "8000:8000"\n  db:\n', encoding="utf-8")

    assert staging_preflight.api_port_is_private(internal)
    assert not staging_preflight.api_port_is_private(public)


def test_telemetry_redaction_removes_url_and_header_credentials():
    raw = (
        "postgresql://oae:password@db:5432/oae\n"
        "Authorization: Bearer key-123\n"
        '{"api_key": "key-456"}\n'
    )

    redacted = collect_staging_telemetry.redact(raw)

    assert "password" not in redacted
    assert "key-123" not in redacted
    assert "key-456" not in redacted
    assert "[REDACTED]" in redacted


def test_sandbox_context_marks_unavailable_host_infrastructure_unknown():
    checks = [
        staging_preflight.Check("docker_cli", "FAIL", "Docker is unavailable."),
        staging_preflight.Check("environment_value_safety", "FAIL", "Placeholder detected."),
    ]

    contextual = staging_preflight.apply_execution_context(checks, "sandbox")

    assert contextual[0].status == "UNKNOWN"
    assert contextual[1].status == "FAIL"
