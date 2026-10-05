import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from oae.api.config import settings
from oae.api.db import db
from oae.api.github import GitHubPublicAnalyzer
from oae.api.mission_results import build_result
from oae.api.workspace_manager import WorkspaceManager
from oae.api.workspace_models import WorkspacePurpose
from oae.core.repository_quality_gate import RepositoryQualityGate
from oae.core.repository_worktree import RepositoryWorktree
from oae.core.vertical_slice_mission import VerticalSliceMission

logger = logging.getLogger("oae.api.job_runner")


class JobRunner:
    """Executes supported engineering operations in isolated mission workspaces."""

    def run(self, job_id: str) -> None:
        with db() as conn:
            row = conn.execute(
                "SELECT operation,payload,tenant_id FROM jobs WHERE id=?",
                (job_id,),
            ).fetchone()
            if not row:
                return
            operation, payload_json, tenant_id = row
            conn.execute(
                "UPDATE jobs SET status='running',updated_at=? WHERE id=?",
                (self._now(), job_id),
            )

        try:
            payload = json.loads(payload_json)
            result = self._dispatch(operation, payload, job_id, tenant_id=str(tenant_id))
            status = "completed"
        except Exception as exc:
            logger.error(
                "job_execution_failed",
                extra={"job_id": job_id, "operation": operation, "error_type": type(exc).__name__},
            )
            result = {
                "schema_version": "1.0",
                "operation": operation,
                "summary": "Mission execution failed before a verified engineering result was produced.",
                "evidence": {"failure_code": "mission_execution_failed"},
                "error": "mission_execution_failed",
            }
            status = "failed"

        with db() as conn:
            conn.execute(
                "UPDATE jobs SET status=?,result=?,updated_at=? WHERE id=?",
                (status, json.dumps(result), self._now(), job_id),
            )

    def _dispatch(
        self,
        operation: str,
        payload: dict,
        job_id: str,
        tenant_id: str | None = None,
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

        if operation == "build":
            stage = payload.get("stage", "bootstrap")
            if stage == "provision":
                return self._provision_workspace(payload, tenant_id)
            if stage in {"validate", "readiness"}:
                return self._validate_workspace(payload, tenant_id, stage)
            if stage in {"attach", "branch", "write", "delete", "diff", "commit"}:
                return self._worktree_operation(payload, tenant_id, stage)

            name = payload.get("name")
            description = payload.get("description")
            if not name or not description:
                raise ValueError("build requires payload.name and payload.description")
            workspace = Path(settings.workspace_root) / "bootstrap" / job_id
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
                evidence={"mission": result, "workspace": str(workspace), "workspace_persistent": True},
            )

        raise ValueError(f"Unsupported operation: {operation}")

    @staticmethod
    def _provision_workspace(payload: dict, tenant_id: str | None) -> dict:
        if not tenant_id:
            raise ValueError("Workspace provisioning requires a tenant context.")
        repository_id = payload.get("repository_id")
        revision_id = payload.get("revision_id")
        if not repository_id or not revision_id:
            raise ValueError("provision requires repository_id and revision_id")
        purpose = WorkspacePurpose(payload.get("purpose", "source"))
        record, manifest = WorkspaceManager().provision(
            tenant_id=tenant_id,
            repository_id=repository_id,
            revision_id=revision_id,
            purpose=purpose,
            parent_workspace_id=payload.get("parent_workspace_id"),
        )
        return build_result(
            operation="build",
            payload=payload,
            repository=repository_id,
            summary=f"Repository revision materialized into workspace {record.id}.",
            evidence={
                "stage": "provision",
                "workspace": record.model_dump(mode="json"),
                "manifest": manifest.model_dump(mode="json"),
                "workspace_persistent": True,
            },
        )

    @staticmethod
    def _validate_workspace(payload: dict, tenant_id: str | None, stage: str) -> dict:
        if not tenant_id:
            raise ValueError("Workspace validation requires a tenant context.")
        workspace_id = payload.get("workspace_id")
        if not workspace_id:
            raise ValueError(f"{stage} requires workspace_id")
        with db(tenant_id) as conn:
            row = conn.execute(
                "SELECT storage_uri,state FROM workspaces WHERE id=? AND tenant_id=?",
                (workspace_id, tenant_id),
            ).fetchone()
        if not row:
            raise ValueError("Workspace not found for tenant.")
        if row[1] != "ready":
            raise ValueError("Workspace must be ready before validation.")
        root = JobRunner._safe_workspace_path(row[0])
        gate = RepositoryQualityGate().run(root)
        gate["stage"] = stage
        gate["workspace_id"] = workspace_id
        return build_result(
            operation="build",
            payload=payload,
            summary=(
                f"Workspace {workspace_id} passed the enabled quality gates."
                if gate["verified"]
                else f"Workspace {workspace_id} remains blocked by the enabled quality gates."
            ),
            evidence={"stage": stage, "quality_gate": gate},
        )

    @staticmethod
    def _worktree_operation(payload: dict, tenant_id: str | None, stage: str) -> dict:
        if not tenant_id:
            raise ValueError("Worktree operations require a tenant context.")
        workspace_id = payload.get("workspace_id")
        if not workspace_id:
            raise ValueError(f"{stage} requires workspace_id")
        with db(tenant_id) as conn:
            row = conn.execute(
                "SELECT storage_uri,repository_id,source_revision_id,state "
                "FROM workspaces WHERE id=? AND tenant_id=?",
                (workspace_id, tenant_id),
            ).fetchone()
            if not row:
                raise ValueError("Workspace not found for tenant.")
            if row[3] != "ready":
                raise ValueError("Workspace must be ready before mutation.")
            repo = conn.execute(
                "SELECT clone_url FROM repositories WHERE id=? AND tenant_id=? AND status='active'",
                (row[1], tenant_id),
            ).fetchone()
            revision = conn.execute(
                "SELECT commit_sha FROM repository_revisions WHERE id=? AND tenant_id=?",
                (row[2], tenant_id),
            ).fetchone()
            if not repo or not revision:
                raise ValueError("Workspace repository revision metadata is unavailable.")
        root = JobRunner._safe_workspace_path(row[0])
        wt = RepositoryWorktree(root)
        if stage == "attach":
            result = wt.attach(clone_url=str(repo[0]), commit_sha=str(revision[0]))
        elif stage == "branch":
            result = wt.create_branch(str(payload.get("branch")))
        elif stage == "write":
            result = wt.write_file(str(payload.get("path")), str(payload.get("content", "")))
        elif stage == "delete":
            result = wt.delete_file(str(payload.get("path")))
        elif stage == "diff":
            result = wt.diff()
        else:
            result = wt.commit(str(payload.get("message")))
        return build_result(
            operation="build",
            payload=payload,
            repository=str(row[1]),
            summary=f"Governed worktree {stage} operation completed.",
            evidence={"stage": stage, "workspace_id": workspace_id, "worktree": result},
        )

    @staticmethod
    def _safe_workspace_path(storage_uri: str) -> Path:
        parsed = urlparse(storage_uri)
        if parsed.scheme != "file" or parsed.netloc not in {"", "localhost"}:
            raise ValueError("Workspace storage URI is not a local governed workspace.")
        root = Path(settings.workspace_root).expanduser().resolve()
        path = Path(parsed.path).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Workspace path escapes the configured workspace root.") from exc
        if not path.is_dir():
            raise ValueError("Workspace storage directory is unavailable.")
        return path

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
