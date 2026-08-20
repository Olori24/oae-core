from __future__ import annotations

from typing import Any

RESULT_SCHEMA_VERSION = "1.0"


def repository_from_payload(payload: dict[str, Any]) -> str | None:
    value = payload.get("repository_url") or payload.get("repository")
    if not value:
        return None
    return str(value).strip() or None


def build_result(
    *,
    operation: str,
    payload: dict[str, Any],
    evidence: dict[str, Any],
    summary: str,
    repository: str | None = None,
) -> dict[str, Any]:
    """Create the stable evidence envelope returned by every SaaS mission."""
    repository = repository or repository_from_payload(payload)
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "operation": operation,
        "summary": summary,
        "evidence": evidence,
    }
    if repository:
        result["repository"] = repository
    return result
