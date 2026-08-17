import json
from datetime import datetime, timezone

from oae.api.db import db
from oae.api.github import GitHubPublicAnalyzer
from oae.api.mission_results import build_result, repository_from_payload


class JobRunner:
    """Executes only explicitly supported, read-only SaaS operations."""

    def run(self, job_id: str) -> None:
        with db() as conn:
            row = conn.execute(
                "SELECT operation,payload FROM jobs WHERE id=?", (job_id,)
            ).fetchone()
            if not row:
                return
            operation, payload_json = row
            conn.execute(
                "UPDATE jobs SET status='running',updated_at=? WHERE id=?",
                (self._now(), job_id),
            )

        try:
            payload = json.loads(payload_json)
            result = self._dispatch(operation, payload)
            status = "completed"
        except Exception as exc:
            result = {
                "schema_version": "1.0",
                "operation": operation,
                "summary": "Mission execution failed before a verified engineering result was produced.",
                "evidence": {"error": str(exc)},
                "error": str(exc),
            }
            status = "failed"

        with db() as conn:
            conn.execute(
                "UPDATE jobs SET status=?,result=?,updated_at=? WHERE id=?",
                (status, json.dumps(result), self._now(), job_id),
            )

    def _dispatch(self, operation: str, payload: dict) -> dict:
        if operation == "analyze":
            repository_url = payload.get("repository_url")
            if not repository_url:
                raise ValueError("analyze requires payload.repository_url")
            analysis = GitHubPublicAnalyzer().analyze(repository_url)
            return {
                **analysis,
                **build_result(
                    operation=operation,
                    payload=payload,
                    repository=analysis.get("repository"),
                    summary=(
                        f"Repository intelligence collected for {analysis['repository']}."
                    ),
                    evidence={
                        "repository_intelligence": analysis,
                    },
                ),
            }

        if operation == "review":
            findings = payload.get("findings", [])
            if not isinstance(findings, list):
                raise ValueError("review requires findings to be a list")
            findings = findings[:100]
            return build_result(
                operation=operation,
                payload=payload,
                summary=f"Engineering review recorded {len(findings)} finding(s).",
                evidence={
                    "finding_count": len(findings),
                    "findings": findings,
                    "review_status": "recorded",
                },
            )

        if operation == "verify":
            verified = bool(payload.get("success"))
            checks = payload.get("checks", [])
            if not isinstance(checks, list):
                raise ValueError("verify requires checks to be a list")
            checks = checks[:100]
            return build_result(
                operation=operation,
                payload=payload,
                summary=(
                    "Verification checks passed."
                    if verified
                    else "Verification checks did not establish success."
                ),
                evidence={
                    "verified": verified,
                    "check_count": len(checks),
                    "checks": checks,
                    "verification_status": "passed" if verified else "not_verified",
                },
            )

        raise ValueError(f"Unsupported operation: {operation}")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
