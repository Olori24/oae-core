import json
import os
import stat
from pathlib import Path

import pytest

from scripts import inject_production_secrets


def source_values() -> dict[str, str]:
    return {
        "API_DOMAIN": "api.oae.example",
        "CADDY_EMAIL": "ops@oae.example",
        "POSTGRES_PASSWORD": "url-safe-password_123",
        "API_KEY_PEPPER": "url-safe-pepper_456",
        "SECRET_KEY": "url-safe-secret_789",
        "ALLOWED_HOSTS": '["api.oae.example"]',
        "DATABASE_URL": "postgresql://oae:url-safe-password_123@db:5432/oae",
    }


def write_source(path: Path, values: dict[str, str], mode: int = 0o600) -> None:
    path.write_text("".join(f"{key}={value}\n" for key, value in values.items()), encoding="utf-8")
    path.chmod(mode)


def production_template() -> str:
    return "\n".join(
        (
            "APP_ENV=production",
            "API_DOMAIN=api.example.com",
            "CADDY_EMAIL=ops@example.com",
            "POSTGRES_DB=oae",
            "POSTGRES_USER=oae",
            "POSTGRES_PASSWORD=",
            "DATABASE_URL=postgresql://oae:${POSTGRES_PASSWORD}@db:5432/oae",
            "API_KEY_PEPPER=",
            "SECRET_KEY=",
            'ALLOWED_HOSTS=["api.example.com"]',
            'CORS_ORIGINS=["https://console.oae.example"]',
            "DURABLE_JOBS_ENABLED=true",
            "REALTIME_EVENTS_ENABLED=true",
            "WORKER_AUTHORIZATION_ENFORCEMENT_ENABLED=false",
        )
    ) + "\n"


def test_injection_writes_atomic_mode_600_target_and_redacted_report(tmp_path: Path):
    template = tmp_path / "template.env"
    source = tmp_path / "source.env"
    target = tmp_path / "target.env"
    values = source_values()
    template.write_text(production_template(), encoding="utf-8")
    write_source(source, values)

    report = inject_production_secrets.inject(template, source, target, replace=False, dry_run=False)
    rendered_report = json.dumps(report.__dict__)

    assert report.status == "PASS"
    assert report.action == "written"
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert "POSTGRES_PASSWORD=url-safe-password_123" in target.read_text(encoding="utf-8")
    assert "url-safe-password_123" not in rendered_report
    assert "url-safe-pepper_456" not in rendered_report


def test_injection_requires_protected_complete_source_and_safe_values(tmp_path: Path):
    template = tmp_path / "template.env"
    source = tmp_path / "source.env"
    template.write_text(production_template(), encoding="utf-8")
    values = source_values()
    values.pop("SECRET_KEY")
    write_source(source, values, mode=0o644)

    with pytest.raises(inject_production_secrets.InjectionError, match="permissions"):
        inject_production_secrets.inject(template, source, tmp_path / "target.env", False, True)

    write_source(source, values)
    with pytest.raises(inject_production_secrets.InjectionError, match="SECRET_KEY"):
        inject_production_secrets.inject(template, source, tmp_path / "target.env", False, True)

    values = source_values()
    values["SECRET_KEY"] = "unsafe secret value"
    write_source(source, values)
    with pytest.raises(inject_production_secrets.InjectionError, match="shell-sensitive"):
        inject_production_secrets.inject(template, source, tmp_path / "target.env", False, True)


def test_injection_refuses_target_overwrite_and_protected_target_requirements(tmp_path: Path):
    template = tmp_path / "template.env"
    source = tmp_path / "source.env"
    target = tmp_path / "target.env"
    template.write_text(production_template(), encoding="utf-8")
    write_source(source, source_values())
    target.write_text("previous=content\n", encoding="utf-8")
    target.chmod(0o600)

    with pytest.raises(inject_production_secrets.InjectionError, match="--replace"):
        inject_production_secrets.inject(template, source, target, False, False)

    target.chmod(0o644)
    with pytest.raises(inject_production_secrets.InjectionError, match="permissions"):
        inject_production_secrets.inject(template, source, target, True, False)


def test_dry_run_does_not_create_target_file(tmp_path: Path):
    template = tmp_path / "template.env"
    source = tmp_path / "source.env"
    target = tmp_path / "target.env"
    template.write_text(production_template(), encoding="utf-8")
    write_source(source, source_values())

    report = inject_production_secrets.inject(template, source, target, False, True)

    assert report.action == "dry_run"
    assert not target.exists()


def test_injection_rejects_a_missing_target_directory_without_rendering_source_values(tmp_path: Path):
    template = tmp_path / "template.env"
    source = tmp_path / "source.env"
    template.write_text(production_template(), encoding="utf-8")
    write_source(source, source_values())

    with pytest.raises(inject_production_secrets.InjectionError, match="parent directory"):
        inject_production_secrets.inject(
            template,
            source,
            tmp_path / "missing" / "target.env",
            False,
            False,
        )


def test_source_file_cannot_be_a_symlink(tmp_path: Path):
    template = tmp_path / "template.env"
    source = tmp_path / "source.env"
    linked_source = tmp_path / "linked-source.env"
    template.write_text(production_template(), encoding="utf-8")
    write_source(source, source_values())
    os.symlink(source, linked_source)

    with pytest.raises(inject_production_secrets.InjectionError, match="non-symlink"):
        inject_production_secrets.inject(template, linked_source, tmp_path / "target.env", False, True)
