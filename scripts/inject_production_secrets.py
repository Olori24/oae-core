#!/usr/bin/env python3
"""Assemble a protected OAE production environment file from host-managed secrets.

The source file must exist only on the deployment host, be a non-symlink regular
file with mode 0600 or stricter, and contain the seven required values. This script
never prints source values or generated environment-file contents.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import tempfile
from dataclasses import asdict, dataclass
from importlib import import_module
from pathlib import Path

preflight = import_module(
    ".staging_preflight" if __package__ else "staging_preflight",
    package=__package__,
)
placeholder_check = import_module(
    ".check_environment_placeholders" if __package__ else "check_environment_placeholders",
    package=__package__,
)

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_INJECTED_KEYS = (
    "API_DOMAIN",
    "CADDY_EMAIL",
    "POSTGRES_PASSWORD",
    "API_KEY_PEPPER",
    "SECRET_KEY",
    "ALLOWED_HOSTS",
    "DATABASE_URL",
)
SAFE_VALUE_PATTERN = re.compile(r"^[A-Za-z0-9._~:/@%+=,?&;{}\[\]-]+$")
ALLOWED_HOSTS_PATTERN = re.compile(
    r'^\["(?:[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?)"(?:,"(?:[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?)")*\]$'
)
DOMAIN_PATTERN = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@dataclass(frozen=True)
class InjectionReport:
    status: str
    action: str
    target_file: str
    variables: tuple[str, ...]
    detail: str


class InjectionError(ValueError):
    """Raised for a non-secret host-handoff configuration failure."""


def require_protected_regular_file(path: Path, label: str) -> None:
    """Require a host-side regular file that is not accessible to group or other users."""
    try:
        metadata = path.lstat()
    except FileNotFoundError as error:
        raise InjectionError(f"{label} does not exist.") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise InjectionError(f"{label} must be a non-symlink regular file.")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise InjectionError(f"{label} permissions must be 0600 or stricter.")


def validate_source_values(values: dict[str, str]) -> None:
    """Validate required source names and a Compose-safe single-line value profile."""
    missing = [key for key in REQUIRED_INJECTED_KEYS if key not in values]
    if missing:
        raise InjectionError(f"Secret source is missing required variable(s): {', '.join(missing)}.")

    for key in REQUIRED_INJECTED_KEYS:
        value = values[key]
        if preflight.has_placeholder(value):
            raise InjectionError(f"Secret source variable {key} is empty or a placeholder.")
        if key == "ALLOWED_HOSTS":
            if not ALLOWED_HOSTS_PATTERN.fullmatch(value):
                raise InjectionError(
                    "Secret source variable ALLOWED_HOSTS must be a compact JSON-style hostname list."
                )
            continue
        if not SAFE_VALUE_PATTERN.fullmatch(value):
            raise InjectionError(
                f"Secret source variable {key} contains unsupported whitespace or shell-sensitive characters."
            )

    if not DOMAIN_PATTERN.fullmatch(values["API_DOMAIN"]):
        raise InjectionError("Secret source variable API_DOMAIN must be a DNS hostname.")
    if not EMAIL_PATTERN.fullmatch(values["CADDY_EMAIL"]):
        raise InjectionError("Secret source variable CADDY_EMAIL must be an email address.")


def parse_environment_text(content: str) -> dict[str, str]:
    """Parse generated dotenv text without writing it or rendering its values."""
    values: dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip():
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def render_target(template: str, source_values: dict[str, str]) -> str:
    """Replace only the named production values while preserving the template contract."""
    replacements = set()
    rendered_lines: list[str] = []
    for raw_line in template.splitlines(keepends=True):
        if raw_line.lstrip().startswith("#") or "=" not in raw_line:
            rendered_lines.append(raw_line)
            continue
        key, _value = raw_line.split("=", 1)
        key = key.strip()
        if key not in REQUIRED_INJECTED_KEYS:
            rendered_lines.append(raw_line)
            continue
        line_ending = "\n" if raw_line.endswith("\n") else ""
        rendered_lines.append(f"{key}={source_values[key]}{line_ending}")
        replacements.add(key)

    absent = [key for key in REQUIRED_INJECTED_KEYS if key not in replacements]
    if absent:
        raise InjectionError(f"Production template is missing injected variable(s): {', '.join(absent)}.")
    return "".join(rendered_lines)


def target_readiness(rendered: str) -> None:
    """Reject output that still has an unresolved required or declared placeholder."""
    values = parse_environment_text(rendered)
    failures = [
        item.name
        for item in placeholder_check.assess_values(values)
        if item.status == "FAIL"
    ]
    if failures:
        raise InjectionError(
            f"Generated production environment still has unresolved variable(s): {', '.join(failures)}."
        )


def atomic_write(target: Path, content: str, replace: bool) -> None:
    """Write a mode-0600 target atomically and never follow an existing symlink."""
    if target.exists() or target.is_symlink():
        if not replace:
            raise InjectionError("Target file exists; use --replace after reviewing the host file.")
        require_protected_regular_file(target, "Existing target file")
    if not target.parent.is_dir():
        raise InjectionError("Target parent directory does not exist.")

    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent, text=True)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        os.chmod(target, 0o600)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise InjectionError("Could not atomically write the protected target file.") from error


def inject(template_file: Path, source_file: Path, target_file: Path, replace: bool, dry_run: bool) -> InjectionReport:
    """Assemble an OAE production environment file without exposing source values."""
    require_protected_regular_file(source_file, "Secret source file")
    if not template_file.is_file():
        raise InjectionError("Production template file does not exist.")
    source_values = preflight.parse_env_file(source_file)
    validate_source_values(source_values)
    rendered = render_target(template_file.read_text(encoding="utf-8"), source_values)
    target_readiness(rendered)
    if not dry_run:
        atomic_write(target_file, rendered, replace)
    return InjectionReport(
        status="PASS",
        action="dry_run" if dry_run else "written",
        target_file=str(target_file),
        variables=REQUIRED_INJECTED_KEYS,
        detail="Protected production environment file is ready for the next preflight.",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=ROOT / ".env.production.example")
    parser.add_argument("--source-file", type=Path, required=True)
    parser.add_argument("--target-file", type=Path, required=True)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    try:
        report = inject(
            args.template,
            args.source_file,
            args.target_file,
            args.replace,
            args.dry_run,
        )
        exit_code = 0
    except InjectionError as error:
        report = InjectionReport(
            status="FAIL",
            action="none",
            target_file=str(args.target_file),
            variables=REQUIRED_INJECTED_KEYS,
            detail=str(error),
        )
        exit_code = 1

    rendered = json.dumps(asdict(report), indent=2) + "\n"
    print(rendered, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
        os.chmod(args.report, 0o600)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
