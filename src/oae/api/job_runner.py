import json
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from oae.api.db import db
from oae.api.github import GitHubPublicAnalyzer
from oae.api.mission_results import build_result
from oae.api.worker_authorizations import WorkerAuthorizationRepository
from oae.api.workspace_manager import WorkspaceManager
from oae.api.workspace_models import WorkspacePurpose
from oae.agents.engineering_action_executor import EngineeringActionExecutor
from oae.core.vertical_slice_mission import VerticalSliceMission
from oae.security.kernel import SecurityKernel

logger = logging.getLogger("oae.api.job_runner")


class JobRunner:
    """Executes supported SaaS engineering operations in isolated mission workspaces."""

    def run(self, job_id: str) -> None:
        with db() as conn:
            row = conn.execute("SELECT operation,payload FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                return
            operation, payload_json = row
            conn.execute(
                "UPDATE jobs SET status='running',updated_at=? WHERE id=?",
                (self._now(), job_id),
            )

        try:
            payload = json.loads(payload_json)
            result = self._dispatch(operation, payload, job_id)
            status = "completed"
        except Exception as exc:
            logger.exception("job_execution_failed job_id=%s operation=%s", job_id, operation)
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

    def _dispatch(
        self, operation: str, payload: dict, job_id: str, *, tenant_id: str | None = None,
        authorization_id: str | None = None,
    ) -> dict:
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
                    summary=f"Repository intelligence collected for {analysis['repository']}.",
                    evidence={"repository_intelligence": analysis},
                ),
            }

        if operation == "review":
            findings = payload.get("findings", [])
            if not isinstance(findings, list):
                raise ValueError("review requires findings to be a list")
            findings = findings[:100]
            result = build_result(
                operation=operation,
                payload=payload,
                summary=f"Engineering review recorded {len(findings)} finding(s).",
                evidence={"finding_count": len(findings), "findings": findings, "review_status": "recorded"},
            )
            result.update({"count": len(findings), "findings": findings})
            return result

        if operation == "verify":
            verified = bool(payload.get("success"))
            checks = payload.get("checks", [])
            if not isinstance(checks, list):
                raise ValueError("verify requires checks to be a list")
            checks = checks[:100]
            result = build_result(
                operation=operation,
                payload=payload,
                summary="Verification checks passed." if verified else "Verification checks did not establish success.",
                evidence={
                    "verified": verified,
                    "check_count": len(checks),
                    "checks": checks,
                    "verification_status": "passed" if verified else "not_verified",
                },
            )
            result.update({"verified": verified, "checks": checks})
            return result

        if operation == "repository_mission":
            return self._run_repository_mission(payload, job_id, tenant_id=tenant_id, authorization_id=authorization_id)

        if operation == "build":
            name = payload.get("name")
            description = payload.get("description")
            if not name or not description:
                raise ValueError("build requires payload.name and payload.description")
            workspace = Path(tempfile.gettempdir()) / "oae-missions" / job_id
            result = VerticalSliceMission().run(
                workspace,
                name=name,
                description=description,
                language=payload.get("language", "Python"),
                framework=payload.get("framework", "FastAPI"),
                database=payload.get("database", "SQLite"),
                testing_framework=payload.get("testing_framework", "pytest"),
            )
            return build_result(
                operation=operation,
                payload=payload,
                summary=f"Application mission {name} reached {result['status']} with readiness score {result['readiness_score']}.",
                evidence={"mission": result, "workspace": str(workspace), "workspace_persistent": False},
            )

        raise ValueError(f"Unsupported operation: {operation}")

    def _run_repository_mission(self, payload: dict, job_id: str, *, tenant_id: str | None, authorization_id: str | None) -> dict:
        if not tenant_id or not authorization_id:
            raise ValueError("repository_mission requires durable tenant and authorization context")
        repository_id = payload.get("repository_id")
        revision_id = payload.get("revision_id")
        actions = payload.get("actions")
        commit_message = payload.get("commit_message")
        if not isinstance(repository_id, str) or not repository_id:
            raise ValueError("repository_mission requires repository_id")
        if not isinstance(revision_id, str) or not revision_id:
            raise ValueError("repository_mission requires revision_id")
        if not isinstance(actions, list) or not actions or len(actions) > 100:
            raise ValueError("repository_mission requires 1-100 actions")
        authorization = WorkerAuthorizationRepository().get(tenant_id=tenant_id, authorization_id=authorization_id)
        if not authorization or authorization.status != "approved" or authorization.expires_at <= datetime.now(timezone.utc):
            raise PermissionError("repository mission authorization is missing or expired")
        if authorization.operation != "repository_mission":
            raise PermissionError("authorization operation does not permit repository missions")
        if authorization.scope.get("repository_id") != repository_id or authorization.scope.get("revision_id") != revision_id:
            raise PermissionError("authorization scope does not match the requested repository revision")
        allowed = {x.strip() for x in authorization.scope.get("allowed_operations", "").split(",") if x.strip()}
        supported = {"create_file", "modify_file", "create_branch", "run_tests", "commit_changes"}
        normalized_actions = []
        for action in actions:
            if not isinstance(action, dict) or not isinstance(action.get("operation"), str):
                raise ValueError("repository mission actions must be operation objects")
            op = action["operation"]
            if op not in supported or op not in allowed:
                raise PermissionError(f"repository operation is not permitted: {op}")
            normalized = dict(action)
            normalized.pop("workspace_path", None)
            normalized_actions.append(normalized)
        ops = {a["operation"] for a in normalized_actions}
        if "commit_changes" in ops:
            if "create_branch" not in ops or not isinstance(commit_message, str) or not commit_message.strip():
                raise ValueError("commit_changes requires create_branch and commit_message")
        record, _manifest = WorkspaceManager().provision(
            tenant_id=tenant_id, repository_id=repository_id, revision_id=revision_id, purpose=WorkspacePurpose.EXECUTION
        )
        workspace = Path(record.storage_uri.removeprefix("file://"))
        security = SecurityKernel()
        if allowed & {"create_file", "modify_file", "create_branch"}:
            security.permissions.allow("write_repository")
            security.approvals.approve("write_repository")
        if "commit_changes" in allowed:
            security.permissions.allow("commit_changes")
            security.approvals.approve("commit_changes")
        if branch := payload.get("branch"):
            if not isinstance(branch, str) or not branch or "create_branch" not in allowed:
                raise PermissionError("branch creation is not authorized")
            normalized_actions.insert(0, {"operation": "create_branch", "branch": branch})
        if commit_message:
            for action in normalized_actions:
                if action["operation"] == "commit_changes":
                    action.setdefault("message", commit_message)
        results = EngineeringActionExecutor(security=security).execute(normalized_actions, workspace_path=workspace)
        if any(item.get("status") != "completed" for item in results):
            raise RuntimeError("repository mission did not complete all requested operations")
        return build_result(
            operation="repository_mission", payload=payload, repository=repository_id,
            summary=f"Repository mission {job_id} completed in a tenant-scoped execution workspace.",
            evidence={"workspace_id": record.id, "workspace": str(workspace), "actions": results, "authorization_id": authorization_id},
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
