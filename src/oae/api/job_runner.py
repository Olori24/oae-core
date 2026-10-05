import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlparse

from oae.api.config import settings
from oae.api.db import db
from oae.api.github import GitHubPublicAnalyzer
from oae.api.github_writer import GitHubRepositoryWriter
from oae.api.mission_results import build_result
from oae.api.workspace_manager import WorkspaceManager
from oae.api.workspace_models import WorkspacePurpose
from oae.core.repository_quality_gate import RepositoryQualityGate
from oae.core.repository_worktree import RepositoryWorktree
from oae.core.governed_execution import run_governed_command, supported_commands
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
            if stage == "sync":
                return self._sync_change_set(payload, tenant_id)
            if stage == "pull_request":
                return self._create_pull_request(payload, tenant_id)
            if stage == "execute":
                return self._execute_command(payload, tenant_id)
            if stage == "verify":
                return self._verify_workspace(payload, tenant_id)

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
    def _sync_change_set(payload: dict, tenant_id: str | None) -> dict:
        if not tenant_id:
            raise ValueError("GitHub synchronization requires a tenant context.")
        workspace_id = payload.get("workspace_id")
        branch = payload.get("branch")
        if not workspace_id or not branch:
            raise ValueError("sync requires workspace_id and branch")
        with db(tenant_id) as conn:
            row = conn.execute(
                "SELECT storage_uri,repository_id,source_revision_id,state FROM workspaces WHERE id=? AND tenant_id=?",
                (workspace_id, tenant_id),
            ).fetchone()
            if not row or row[3] != "ready":
                raise ValueError("Workspace must be ready before synchronization.")
            repo = conn.execute(
                "SELECT clone_url,default_branch FROM repositories WHERE id=? AND tenant_id=? AND status='active'",
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
        local_commit = wt.head()
        files = wt.snapshot_commit()
        writer = GitHubRepositoryWriter(str(repo[0]))
        remote = writer.synchronize(
            base_sha=str(revision[0]),
            branch=str(branch),
            files=files,
            commit_message=str(payload.get("message") or "chore(oae): synchronize governed change set"),
        )
        change_set_id = str(uuid4())
        now = JobRunner._now()
        title = str(payload.get("title") or f"OAE change set {change_set_id[:8]}")
        summary = str(payload.get("summary") or f"Governed change set synchronized from workspace {workspace_id}.")
        with db(tenant_id) as conn:
            conn.execute(
                "INSERT INTO engineering_change_sets "
                "(id,tenant_id,workspace_id,repository_id,source_revision_id,local_commit_sha,remote_commit_sha,"
                "branch_name,status,pr_number,pr_url,title,summary,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (change_set_id,tenant_id,workspace_id,row[1],row[2],local_commit,remote["commit_sha"],
                 branch,"synced",None,None,title,summary,now,now),
            )
            for item in files:
                conn.execute(
                    "INSERT INTO engineering_change_files (id,tenant_id,change_set_id,path,status,created_at) VALUES (?,?,?,?,?,?)",
                    (str(uuid4()),tenant_id,change_set_id,item["path"],item["status"],now),
                )
        return build_result(
            operation="build", payload=payload, repository=str(row[1]),
            summary=f"Change set {change_set_id} synchronized to GitHub branch {branch}.",
            evidence={"stage":"sync","change_set_id":change_set_id,"local_commit_sha":local_commit,"remote":remote,"file_count":len(files)},
        )

    @staticmethod
    def _create_pull_request(payload: dict, tenant_id: str | None) -> dict:
        if not tenant_id:
            raise ValueError("Pull request creation requires a tenant context.")
        change_set_id = payload.get("change_set_id")
        if not change_set_id:
            raise ValueError("pull_request requires change_set_id")
        with db(tenant_id) as conn:
            row = conn.execute(
                "SELECT workspace_id,repository_id,branch_name,status,title,summary,remote_commit_sha "
                "FROM engineering_change_sets WHERE id=? AND tenant_id=?",
                (change_set_id, tenant_id),
            ).fetchone()
            if not row:
                raise ValueError("Change set not found for tenant.")
            repo = conn.execute(
                "SELECT clone_url,default_branch FROM repositories WHERE id=? AND tenant_id=? AND status='active'",
                (row[1], tenant_id),
            ).fetchone()
            if not repo:
                raise ValueError("Change set repository is unavailable.")
        if row[3] not in {"synced", "pr_failed"} or not row[6]:
            raise ValueError("Change set must be synchronized before opening a pull request.")
        writer = GitHubRepositoryWriter(str(repo[0]))
        pr = writer.create_pull_request(
            branch=str(row[2]), base=str(repo[1]),
            title=str(row[4] or "OAE governed change"),
            body=str(row[5] or "Generated by OAE Core. Review the governed change set and CI evidence before merging."),
        )
        with db(tenant_id) as conn:
            conn.execute(
                "UPDATE engineering_change_sets SET status='pr_open',pr_number=?,pr_url=?,updated_at=? WHERE id=? AND tenant_id=?",
                (pr.get("number"),pr.get("html_url"),JobRunner._now(),change_set_id,tenant_id),
            )
        return build_result(
            operation="build", payload=payload, repository=str(row[1]),
            summary=f"Pull request created for change set {change_set_id}.",
            evidence={"stage":"pull_request","change_set_id":change_set_id,"pull_request":{"number":pr.get("number"),"url":pr.get("html_url"),"branch":row[2]}},
        )

    @staticmethod
    def _execute_command(payload: dict, tenant_id: str | None) -> dict:
        if not tenant_id:
            raise ValueError("Command execution requires a tenant context.")
        workspace_id = payload.get("workspace_id")
        command = payload.get("command")
        if not workspace_id or not command:
            raise ValueError("execute requires workspace_id and command")
        if command not in supported_commands():
            raise ValueError(f"Unsupported governed command: {command}")
        with db(tenant_id) as conn:
            row = conn.execute(
                "SELECT storage_uri,repository_id,state FROM workspaces WHERE id=? AND tenant_id=?",
                (workspace_id, tenant_id),
            ).fetchone()
        if not row or row[2] != "ready":
            raise ValueError("Workspace must be ready before command execution.")
        root = JobRunner._safe_workspace_path(row[0])
        result = run_governed_command(command, workspace=root)
        return build_result(
            operation="build",
            payload=payload,
            repository=str(row[1]),
            summary=(
                f"Governed command {command} passed."
                if result["passed"]
                else f"Governed command {command} failed verification."
            ),
            evidence={"stage":"execute","workspace_id":workspace_id,"execution":result},
        )

    @staticmethod
    def _verify_workspace(payload: dict, tenant_id: str | None) -> dict:
        if not tenant_id:
            raise ValueError("Workspace verification requires a tenant context.")
        workspace_id = payload.get("workspace_id")
        commands = payload.get("commands") or ["python_compile", "ruff", "pytest"]
        if not workspace_id:
            raise ValueError("verify requires workspace_id")
        if not isinstance(commands, list) or not commands or len(commands) > 8:
            raise ValueError("verify requires 1 to 8 governed commands")
        if any(command not in supported_commands() for command in commands):
            raise ValueError("verify contains an unsupported governed command")
        with db(tenant_id) as conn:
            row = conn.execute(
                "SELECT storage_uri,repository_id,state FROM workspaces WHERE id=? AND tenant_id=?",
                (workspace_id, tenant_id),
            ).fetchone()
        if not row or row[2] != "ready":
            raise ValueError("Workspace must be ready before verification.")
        root = JobRunner._safe_workspace_path(row[0])
        results = []
        for command in commands:
            result = run_governed_command(command, workspace=root)
            results.append(result)
            if not result["passed"]:
                break
        passed = bool(results) and all(item["passed"] for item in results)
        return build_result(
            operation="build",
            payload=payload,
            repository=str(row[1]),
            summary=(
                f"Workspace {workspace_id} passed {len(results)} governed verification command(s)."
                if passed
                else f"Workspace {workspace_id} failed governed verification."
            ),
            evidence={
                "stage":"verify",
                "workspace_id":workspace_id,
                "verified":passed,
                "commands":results,
                "commands_requested":commands,
            },
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
