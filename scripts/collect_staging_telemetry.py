#!/usr/bin/env python3
"""Collect redacted, host-side governed-execution staging evidence.

Run only after a real staging host has passed the durable or governed preflight.
The utility never reads, prints, or saves Docker environment values.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

try:
    from scripts.staging_preflight import DEFAULT_COMPOSE_FILES, ROOT, parse_env_file, redact
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from staging_preflight import DEFAULT_COMPOSE_FILES, ROOT, parse_env_file, redact

DEFAULT_SERVICES = ("gateway", "api", "worker", "relay", "db")
DATABASE_SUMMARY_SQL = """
SELECT 'migration' AS record_type, name AS key, applied_at::text AS detail
FROM oae_schema_migrations
WHERE name IN (
  '0003_transactional_outbox_sse.sql',
  '0005_worker_authorization_foundation.sql',
  '0006_principal_and_authorization_decision_metadata.sql'
)
UNION ALL
SELECT 'authorization_status', operation || ':' || status, count(*)::text
FROM worker_authorizations
GROUP BY operation, status
UNION ALL
SELECT 'outbox_event_type', event_type, count(*)::text
FROM outbox_events
WHERE event_type LIKE 'authorization.%'
GROUP BY event_type
UNION ALL
SELECT 'realtime_event_type', event_type, count(*)::text
FROM realtime_events
WHERE event_type LIKE 'authorization.%'
GROUP BY event_type
ORDER BY record_type, key;
""".strip()


def compose_command(compose_files: list[Path], env_file: Path, args: list[str]) -> list[str]:
    command = ["docker", "compose", "--env-file", str(env_file)]
    for compose_file in compose_files:
        command.extend(["-f", str(compose_file)])
    return [*command, *args]


def run(command: list[str]) -> tuple[int, str]:
    try:
        completed = subprocess.run(  # noqa: S603
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 2, f"command error: {type(exc).__name__}"
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
    return completed.returncode, redact(output) + ("\n" if output else "")


def write_evidence(path: Path, status: int, content: str) -> None:
    prefix = f"collection_status={status}\n"
    path.write_text(prefix + redact(content), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env.production")
    parser.add_argument(
        "--compose-file", type=Path, action="append", default=list(DEFAULT_COMPOSE_FILES)
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--since", default="30m")
    parser.add_argument("--tail", type=int, default=300)
    parser.add_argument("--trace-id", default="not-provided")
    parser.add_argument("--service", action="append", dest="services", default=[])
    args = parser.parse_args()

    if shutil.which("docker") is None:
        print("Docker CLI is unavailable; no telemetry was collected.")
        return 2
    if not args.env_file.exists() or not all(path.exists() for path in args.compose_file):
        print("Environment or Compose file is unavailable; no telemetry was collected.")
        return 2

    values = parse_env_file(args.env_file)
    for key in ("POSTGRES_DB", "POSTGRES_USER"):
        if not values.get(key):
            print(f"Required database configuration key is absent: {key}.")
            return 2

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    services = tuple(args.services) if args.services else DEFAULT_SERVICES
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "trace_id": redact(args.trace_id),
        "repository_revision": run(["git", "rev-parse", "HEAD"])[1].strip(),
        "services": list(services),
        "redaction": "Common bearer, API key, authorization header, URL-password, and dotenv secret patterns were redacted.",
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(redact(json.dumps(manifest)), indent=2) + "\n", encoding="utf-8"
    )

    status, content = run(compose_command(args.compose_file, args.env_file, ["ps", "--format", "json"]))
    write_evidence(output_dir / "compose-ps.log", status, content)

    for service in services:
        status, content = run(
            compose_command(
                args.compose_file,
                args.env_file,
                ["logs", "--no-color", "--timestamps", "--since", args.since, "--tail", str(args.tail), service],
            )
        )
        write_evidence(output_dir / f"{service}.log", status, content)

    status, content = run(
        compose_command(
            args.compose_file,
            args.env_file,
            [
                "exec",
                "-T",
                "db",
                "psql",
                "-U",
                values["POSTGRES_USER"],
                "-d",
                values["POSTGRES_DB"],
                "-v",
                "ON_ERROR_STOP=1",
                "-At",
                "-c",
                DATABASE_SUMMARY_SQL,
            ],
        )
    )
    write_evidence(output_dir / "database-summary.log", status, content)
    print(f"Redacted telemetry evidence written to {output_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
