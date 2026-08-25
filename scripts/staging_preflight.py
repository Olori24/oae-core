#!/usr/bin/env python3
"""Run non-secret readiness checks before OAE real-host staging validation.

The script intentionally reports only key names, boolean feature states, public DNS
answers, and command outcomes. It never prints environment values or Docker config.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import socket
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPOSE_FILES = (
    ROOT / "docker-compose.production.yml",
    ROOT / "docker-compose.staging.yml",
)
REQUIRED_KEYS = (
    "APP_ENV",
    "API_DOMAIN",
    "CADDY_EMAIL",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "DATABASE_URL",
    "API_KEY_PEPPER",
    "ALLOWED_HOSTS",
    "CORS_ORIGINS",
    "DURABLE_JOBS_ENABLED",
    "REALTIME_EVENTS_ENABLED",
    "WORKER_AUTHORIZATION_ENFORCEMENT_ENABLED",
)
STAGE_FLAGS = {
    "bootstrap": {
        "DURABLE_JOBS_ENABLED": "false",
        "REALTIME_EVENTS_ENABLED": "false",
        "WORKER_AUTHORIZATION_ENFORCEMENT_ENABLED": "false",
    },
    "durable": {
        "DURABLE_JOBS_ENABLED": "true",
        "REALTIME_EVENTS_ENABLED": "true",
        "WORKER_AUTHORIZATION_ENFORCEMENT_ENABLED": "false",
    },
    "governed": {
        "DURABLE_JOBS_ENABLED": "true",
        "REALTIME_EVENTS_ENABLED": "true",
        "WORKER_AUTHORIZATION_ENFORCEMENT_ENABLED": "true",
    },
}
SENSITIVE_KEY_PATTERN = re.compile(
    r"(password|secret|token|pepper|authorization|api[_-]?key|cookie)", re.IGNORECASE
)
PLACEHOLDER_PATTERN = re.compile(r"(replace|change.?me|example\.com|<[^>]+>)", re.IGNORECASE)


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


def parse_env_file(path: Path) -> dict[str, str]:
    """Read simple dotenv assignments without expanding or displaying their values."""
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            values[key] = value.strip().strip('"').strip("'")
    return values


def has_placeholder(value: str) -> bool:
    return not value or bool(PLACEHOLDER_PATTERN.search(value))


def environment_checks(values: dict[str, str], stage: str) -> list[Check]:
    """Validate configuration presence and safety gates without exposing secrets."""
    checks: list[Check] = []
    missing = [key for key in REQUIRED_KEYS if key not in values]
    checks.append(
        Check(
            "required_environment_keys",
            "PASS" if not missing else "FAIL",
            "All required environment keys are present."
            if not missing
            else f"Missing keys: {', '.join(missing)}.",
        )
    )

    unsafe = [
        key
        for key in ("API_DOMAIN", "CADDY_EMAIL", "POSTGRES_PASSWORD", "API_KEY_PEPPER")
        if key in values and has_placeholder(values[key])
    ]
    checks.append(
        Check(
            "environment_value_safety",
            "PASS" if not unsafe else "FAIL",
            "Required non-placeholder values are configured."
            if not unsafe
            else f"Unset or placeholder values detected for: {', '.join(unsafe)}.",
        )
    )

    expected = STAGE_FLAGS[stage]
    mismatched = [
        key
        for key, target in expected.items()
        if values.get(key, "").strip().lower() != target
    ]
    checks.append(
        Check(
            "feature_flag_stage",
            "PASS" if not mismatched else "FAIL",
            f"Feature flags match the {stage} stage."
            if not mismatched
            else f"Feature flags do not match the {stage} stage: {', '.join(mismatched)}.",
        )
    )
    return checks


def command_check(name: str, command: list[str]) -> Check:
    """Run a read-only local command and avoid returning its potentially sensitive output."""
    try:
        completed = subprocess.run(  # noqa: S603
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return Check(name, "FAIL", "Command could not be completed.")
    return Check(
        name,
        "PASS" if completed.returncode == 0 else "FAIL",
        "Command completed successfully."
        if completed.returncode == 0
        else f"Command exited with status {completed.returncode}.",
    )


def compose_command(compose_files: Iterable[Path], env_file: Path, args: list[str]) -> list[str]:
    command = ["docker", "compose", "--env-file", str(env_file)]
    for compose_file in compose_files:
        command.extend(["-f", str(compose_file)])
    return [*command, *args]


def api_port_is_private(compose_file: Path) -> bool:
    """Return whether the API service lacks a host-side 8000 port publication."""
    text = compose_file.read_text(encoding="utf-8")
    match = re.search(r"^  api:\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:|\Z)", text, re.MULTILINE | re.DOTALL)
    if match is None:
        return False
    return not re.search(r"^\s*-\s*[\"']?[^\n\"']*:8000[\"']?\s*$", match.group("body"), re.MULTILINE)


def dns_check(domain: str) -> Check:
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(domain, 443)})
    except socket.gaierror:
        return Check("public_dns", "FAIL", "API_DOMAIN did not resolve for HTTPS.")
    return Check("public_dns", "PASS", f"API_DOMAIN resolved to {', '.join(map(str, addresses))}.")


def redact(text: str) -> str:
    """Redact common credentials from diagnostic text before it reaches a report."""
    text = re.sub(
        r"(?i)(postgres(?:ql)?://[^:\s/]+:)([^@\s]+)(@)", r"\1[REDACTED]\3", text
    )
    text = re.sub(r"(?i)(bearer\s+)[^\s]+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(authorization:\s*)[^\r\n]+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(x-api-key:\s*)[^\r\n]+", r"\1[REDACTED]", text)
    text = re.sub(
        r"(?im)^\s*([A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|PEPPER|API_KEY)[A-Z0-9_]*)\s*=\s*.*$",
        r"\1=[REDACTED]",
        text,
    )
    text = re.sub(
        r"(?i)([\"']?[a-z0-9_-]*(?:password|secret|token|pepper|api[_-]?key)[a-z0-9_-]*[\"']?\s*[:=]\s*)"
        r"(?:\"[^\"]*\"|'[^']*'|[^,\s}\]]+)",
        r"\1[REDACTED]",
        text,
    )
    return text


def apply_execution_context(checks: list[Check], execution_context: str) -> list[Check]:
    """Mark sandbox-only infrastructure gaps as unknown, never as a passing host control."""
    if execution_context != "sandbox":
        return checks
    host_only = {"docker_cli", "docker_compose", "compose_configuration", "public_dns"}
    return [
        Check(
            check.name,
            "UNKNOWN" if check.name in host_only and check.status == "FAIL" else check.status,
            check.detail,
        )
        for check in checks
    ]


def build_report(args: argparse.Namespace) -> tuple[list[Check], str]:
    checks: list[Check] = []
    if not args.env_file.exists():
        return [Check("environment_file", "FAIL", "Environment file does not exist.")], ""

    values = parse_env_file(args.env_file)
    checks.append(Check("environment_file", "PASS", "Environment file is readable."))
    checks.extend(environment_checks(values, args.stage))

    compose_exists = all(path.exists() for path in args.compose_file)
    checks.append(
        Check(
            "compose_files",
            "PASS" if compose_exists else "FAIL",
            "All Compose files are present." if compose_exists else "One or more Compose files are missing.",
        )
    )
    if args.compose_file and args.compose_file[0].exists():
        checks.append(
            Check(
                "api_port_private",
                "PASS" if api_port_is_private(args.compose_file[0]) else "FAIL",
                "API port 8000 is not published by the API service."
                if api_port_is_private(args.compose_file[0])
                else "API service publishes a host-side port or could not be inspected.",
            )
        )

    docker_available = shutil.which("docker") is not None
    checks.append(
        Check(
            "docker_cli",
            "PASS" if docker_available else "FAIL",
            "Docker CLI is available." if docker_available else "Docker CLI is not available on this host.",
        )
    )
    if docker_available and compose_exists:
        checks.append(command_check("docker_compose", ["docker", "compose", "version"]))
        checks.append(
            command_check(
                "compose_configuration",
                compose_command(args.compose_file, args.env_file, ["config", "--quiet"]),
            )
        )

    if values.get("API_DOMAIN") and not has_placeholder(values["API_DOMAIN"]):
        checks.append(dns_check(values["API_DOMAIN"]))
    else:
        checks.append(Check("public_dns", "FAIL", "API_DOMAIN is unset or a placeholder."))

    revision = ""
    try:
        revision = subprocess.check_output(  # noqa: S603
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, timeout=10
        ).strip()
    except (OSError, subprocess.SubprocessError):
        checks.append(Check("repository_revision", "FAIL", "Could not resolve repository revision."))
    else:
        expected = args.expected_revision
        checks.append(
            Check(
                "repository_revision",
                "PASS" if not expected or revision == expected else "FAIL",
                "Repository revision is available."
                if not expected or revision == expected
                else "Repository revision differs from the expected revision.",
            )
        )
    return apply_execution_context(checks, args.execution_context), revision


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env.production")
    parser.add_argument(
        "--compose-file",
        type=Path,
        action="append",
        default=list(DEFAULT_COMPOSE_FILES),
        help="Compose file to include. Repeat to override the default production and staging pair.",
    )
    parser.add_argument("--stage", choices=tuple(STAGE_FLAGS), default="bootstrap")
    parser.add_argument(
        "--execution-context",
        choices=("host", "sandbox"),
        default="host",
        help="Use sandbox only when rehearsing without a real staging host.",
    )
    parser.add_argument("--expected-revision", help="Expected Git commit SHA, if deployment is pinned.")
    parser.add_argument("--report", type=Path, help="Optional path for the sanitized JSON report.")
    args = parser.parse_args()

    checks, revision = build_report(args)
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "execution_context": args.execution_context,
        "stage": args.stage,
        "repository_revision": revision,
        "checks": [asdict(check) for check in checks],
    }
    rendered = json.dumps(report, indent=2) + "\n"
    print(redact(rendered))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(redact(rendered), encoding="utf-8")
    return 1 if any(check.status == "FAIL" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
