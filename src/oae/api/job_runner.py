import json
from datetime import datetime, timezone

from oae.api.db import db
from oae.api.github import GitHubPublicAnalyzer


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
            result = {"error": str(exc)}
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
            return GitHubPublicAnalyzer().analyze(repository_url)
        if operation == "review":
            findings = payload.get("findings", [])
            if not isinstance(findings, list):
                raise ValueError("review requires findings to be a list")
            return {"count": len(findings), "findings": findings[:100]}
        if operation == "verify":
            return {"verified": bool(payload.get("success")), "checks": payload.get("checks", [])}
        raise ValueError(f"Unsupported operation: {operation}")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
