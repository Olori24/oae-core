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
from oae.core.engineering_planner import build_engineering_plan
from oae.core.autonomous_agent import next_agent_decision
from oae.core.ci_inspector import GitHubCiInspector
from oae.core.production_readiness import evaluate_production_readiness
from oae.core.vertical_slice_mission import VerticalSliceMission
from oae.api.agent_runs import AgentRunRepository
from oae.api.durable_jobs import DurableJobRepository
from oae.core.agent_action_executor import execute_agent_action
from oae.core.coding_brain import CodingBrain
from oae.core.coding_executor import apply_coding_proposal
from oae.providers.open_weight import OpenWeightModelGateway, open_weight_config_from_settings

logger = logging.getLogger("oae.api.job_runner")


class JobRunner:
    """Executes supported engineering operations in isolated mission workspaces."""

    def run(self, job_id: str) -> None:
        with db() as conn:
            row = conn.execute(
                "SELECT operation,payload,tenant_id,authorization_id FROM jobs WHERE id=?",
                (job_id,),
            ).fetchone()
            if not row:
                return
            operation, payload_json, tenant_id, authorization_id = row
            conn.execute(
                "UPDATE jobs SET status='running',updated_at=? WHERE id=?",
                (self._now(), job_id),
            )

        try:
            payload = json.loads(payload_json)
            if authorization_id:
                payload["_authorization_id"] = str(authorization_id)
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
            if stage == "plan":
                return self._create_engineering_plan(payload, tenant_id)
            if stage == "agent":
                return self._next_agent_action(payload, tenant_id)
            if stage == "coding_proposal":
                return self._coding_proposal(payload, tenant_id)
            if stage == "coding_execute":
                return self._coding_execute(payload, tenant_id)
            if stage == "agent_run_start":
                return self._start_agent_run(payload, tenant_id)
            if stage == "agent_run_step":
                return self._record_agent_run_step(payload, tenant_id)
            if stage == "agent_tick":
                return self._agent_tick(payload, tenant_id, job_id)
            if stage == "ci_status":
                return self._inspect_ci_status(payload, tenant_id)
            if stage == "readiness_gate":
                return self._evaluate_readiness_gate(payload, tenant_id)

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
    def _create_engineering_plan(payload: dict, tenant_id: str | None) -> dict:
        if not tenant_id:
            raise ValueError("Planning requires a tenant context.")
        workspace_id = payload.get("workspace_id")
        if not workspace_id:
            raise ValueError("plan requires workspace_id")
        plan = build_engineering_plan(
            objective=str(payload.get("objective", "")),
            repository_kind=str(payload.get("repository_kind", "unknown")),
            has_tests=bool(payload.get("has_tests", True)),
            has_linter=bool(payload.get("has_linter", True)),
            has_typecheck=bool(payload.get("has_typecheck", False)),
            has_build=bool(payload.get("has_build", False)),
            test_runner=str(payload.get("test_runner", "none")),
            security_required=bool(payload.get("security_required", True)),
            action_inputs=payload.get("action_inputs") if isinstance(payload.get("action_inputs"), dict) else None,
        )
        return build_result(
            operation="build",
            payload=payload,
            summary=f"Engineering plan created for workspace {workspace_id}.",
            evidence={"stage": "plan", "workspace_id": workspace_id, "plan": plan.to_dict()},
        )

    @staticmethod
    def _next_agent_action(payload: dict, tenant_id: str | None) -> dict:
        if not tenant_id:
            raise ValueError("Agent control requires a tenant context.")
        plan = payload.get("plan")
        completed = payload.get("completed_steps") or []
        if not isinstance(plan, dict) or not isinstance(completed, list):
            raise ValueError("agent requires a plan object and completed_steps list")
        decision = next_agent_decision(plan, [str(item) for item in completed])
        return build_result(
            operation="build",
            payload=payload,
            summary=f"Agent controller status: {decision.status}.",
            evidence={"stage": "agent", "decision": decision.to_dict()},
        )


    @staticmethod
    def _coding_execute(payload: dict, tenant_id: str | None) -> dict:
        if not tenant_id:
            raise ValueError("Coding execution requires a tenant context.")
        workspace_id = payload.get("workspace_id")
        objective = str(payload.get("objective", "")).strip()
        if not workspace_id or not objective:
            raise ValueError("coding_execute requires workspace_id and objective")
        model = settings.coding_brain_model.strip()
        if not model:
            raise ValueError("Coding brain model is not configured server-side.")
        with db(tenant_id) as conn:
            row = conn.execute(
                "SELECT storage_uri,state,repository_id FROM workspaces WHERE id=? AND tenant_id=?",
                (workspace_id, tenant_id),
            ).fetchone()
        if not row or row[1] != "ready":
            raise ValueError("Workspace must be ready before coding execution.")
        root = self._safe_workspace_path(row[0])
        gateway = OpenWeightModelGateway(open_weight_config_from_settings(settings))
        proposal = CodingBrain(gateway, model).propose(
            tenant_id=tenant_id, workspace=root, objective=objective
        )
        worktree = RepositoryWorktree(root)
        evidence = apply_coding_proposal(
            proposal=proposal,
            workspace=root,
            write_file=worktree.write_file,
            delete_file=worktree.delete_file,
        )
        verification = []
        for command in proposal.verification:
            result = run_governed_command(command, workspace=root)
            verification.append(result)
            if not result.get("passed"):
                return build_result(
                    operation="build",
                    payload=payload,
                    summary="Coding proposal applied but verification failed.",
                    evidence={
                        "stage": "coding_execute",
                        "workspace_id": workspace_id,
                        "proposal": proposal.to_dict(),
                        "mutations": evidence,
                        "verification": verification,
                        "verified": False,
                    },
                )
        return build_result(
            operation="build",
            payload=payload,
            summary="OAE generated, applied, and verified a coding proposal.",
            evidence={
                "stage": "coding_execute",
                "workspace_id": workspace_id,
                "proposal": proposal.to_dict(),
                "mutations": evidence,
                "verification": verification,
                "verified": True,
            },
        )

    @staticmethod
    def _coding_proposal(payload: dict, tenant_id: str | None) -> dict:
        if not tenant_id:
            raise ValueError("Coding proposal requires a tenant context.")
        workspace_id = payload.get("workspace_id")
        objective = str(payload.get("objective", "")).strip()
        if not workspace_id or not objective:
            raise ValueError("coding_proposal requires workspace_id and objective")
        model = settings.coding_brain_model.strip()
        if not model:
            raise ValueError("Coding brain model is not configured server-side.")
        with db(tenant_id) as conn:
            row = conn.execute(
                "SELECT storage_uri,state FROM workspaces WHERE id=? AND tenant_id=?",
                (workspace_id, tenant_id),
            ).fetchone()
        if not row or row[1] != "ready":
            raise ValueError("Workspace must be ready before coding proposal generation.")
        root = JobRunner._safe_workspace_path(row[0])
        gateway = OpenWeightModelGateway(open_weight_config_from_settings(settings))
        proposal = CodingBrain(gateway, model).propose(
            tenant_id=tenant_id, workspace=root, objective=objective
        )
        return build_result(
            operation="build",
            payload=payload,
            summary=f"Coding proposal generated for workspace {workspace_id}.",
            evidence={"stage": "coding_proposal", "workspace_id": workspace_id, "proposal": proposal.to_dict()},
        )

    @staticmethod
    def _start_agent_run(payload: dict, tenant_id: str | None) -> dict:
        if not tenant_id:
            raise ValueError("Agent run requires a tenant context.")
        workspace_id = payload.get("workspace_id")
        plan = payload.get("plan")
        if not workspace_id or not isinstance(plan, dict):
            raise ValueError("agent_run_start requires workspace_id and plan")
        record = AgentRunRepository().start(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            plan=plan,
            idempotency_key=payload.get("run_idempotency_key"),
            correlation_id=payload.get("correlation_id"),
            max_repairs=int(payload.get("max_repairs", 2)),
        )
        decision = record.state.next_decision()
        if record.state.status == "running":
            authorization_id = record.authorization_id or payload.get("_authorization_id")
            if not authorization_id:
                raise ValueError("Agent run cannot start without worker authorization.")
            DurableJobRepository().enqueue(
                tenant_id=tenant_id,
                operation="build",
                payload={"stage": "agent_tick", "run_id": record.id},
                authorization_id=authorization_id,
                idempotency_key=f"agent-tick:{record.id}:0:0",
                priority=90,
            )
        return build_result(
            operation="build",
            payload=payload,
            summary=f"Agent run {record.id} is {record.state.status}.",
            evidence={
                "stage": "agent_run_start",
                "run_id": record.id,
                "workspace_id": record.workspace_id,
                "status": record.state.status,
                "decision": decision.to_dict(),
                "completed_steps": list(record.state.completed_steps),
            },
        )

    @staticmethod
    def _record_agent_run_step(payload: dict, tenant_id: str | None) -> dict:
        if not tenant_id:
            raise ValueError("Agent run step requires a tenant context.")
        run_id = payload.get("run_id")
        step_id = payload.get("step_id")
        if not run_id or not step_id:
            raise ValueError("agent_run_step requires run_id and step_id")
        record = AgentRunRepository().record_result(
            tenant_id=tenant_id,
            run_id=run_id,
            step_id=step_id,
            success=bool(payload.get("success")),
            evidence=payload.get("evidence") if isinstance(payload.get("evidence"), dict) else None,
        )
        decision = record.state.next_decision() if record.state.status == "running" else None
        return build_result(
            operation="build",
            payload=payload,
            summary=f"Agent run {record.id} recorded step {step_id}.",
            evidence={
                "stage": "agent_run_step",
                "run_id": record.id,
                "status": record.state.status,
                "completed_steps": list(record.state.completed_steps),
                "repair_count": record.state.repair_count,
                "next_decision": decision.to_dict() if decision else None,
            },
        )

    def _agent_tick(self, payload: dict, tenant_id: str | None, job_id: str) -> dict:
        if not tenant_id:
            raise ValueError("Agent tick requires a tenant context.")
        run_id = payload.get("run_id")
        if not run_id:
            raise ValueError("agent_tick requires run_id")
        repository = AgentRunRepository()
        claim = repository.claim_next_action(tenant_id=tenant_id, run_id=run_id)
        if claim is None:
            record = repository.get(tenant_id=tenant_id, run_id=run_id)
            return build_result(
                operation="build",
                payload=payload,
                summary=f"Agent run {run_id} has no claimable action.",
                evidence={"stage": "agent_tick", "run_id": run_id, "status": record.state.status},
            )
        record, token, decision = claim
        step = next(
            (item for item in record.state.plan.get("steps", [])
             if isinstance(item, dict) and item.get("id") == decision.get("step_id")),
            None,
        )
        if step is None:
            repository.record_result(
                tenant_id=tenant_id, run_id=run_id,
                step_id=str(decision["step_id"]), success=False,
                evidence={"failure_code": "planned_step_missing"},
                action_token=token,
            )
            raise ValueError("Claimed agent step is missing from the persisted plan.")

        base_payload = {
            "workspace_id": record.workspace_id,
            "commands": list(record.state.plan.get("verification_commands", [])),
        }
        with db(tenant_id) as conn:
            row = conn.execute(
                "SELECT r.clone_url FROM repositories r JOIN workspaces w ON w.repository_id=r.id "
                "WHERE w.id=? AND w.tenant_id=? AND r.tenant_id=? AND r.status='active'",
                (record.workspace_id, tenant_id, tenant_id),
            ).fetchone()
        if row:
            base_payload["repository_url"] = str(row[0])

        try:
            result = execute_agent_action(
                action=str(decision["action"]),
                step=step,
                workspace_id=record.workspace_id,
                base_payload=base_payload,
                invoke=lambda operation, action_payload: self._dispatch(
                    operation, action_payload, job_id, tenant_id
                ),
            )
            updated = repository.record_result(
                tenant_id=tenant_id,
                run_id=run_id,
                step_id=str(decision["step_id"]),
                success=True,
                evidence={"action": decision, "result": result},
                action_token=token,
            )
        except Exception as exc:
            updated = repository.record_result(
                tenant_id=tenant_id,
                run_id=run_id,
                step_id=str(decision["step_id"]),
                success=False,
                evidence={"action": decision, "failure_code": "agent_action_failed", "error_type": type(exc).__name__},
                action_token=token,
            )
        if updated.state.status == "running":
            DurableJobRepository().enqueue(
                tenant_id=tenant_id,
                operation="build",
                payload={"stage": "agent_tick", "run_id": run_id},
                authorization_id=updated.authorization_id or payload.get("_authorization_id"),
                idempotency_key=f"agent-tick:{run_id}:{updated.state.repair_count}:{len(updated.state.completed_steps)}",
                priority=90,
            )
        return build_result(
            operation="build",
            payload=payload,
            summary=f"Agent run {run_id} advanced through {decision['step_id']}.",
            evidence={
                "stage": "agent_tick",
                "run_id": run_id,
                "decision": decision,
                "status": updated.state.status,
                "completed_steps": list(updated.state.completed_steps),
                "repair_count": updated.state.repair_count,
            },
        )

    @staticmethod
    def _inspect_ci_status(payload: dict, tenant_id: str | None) -> dict:
        if not tenant_id:
            raise ValueError("CI inspection requires a tenant context.")
        workspace_id = payload.get("workspace_id")
        commit_sha = payload.get("commit_sha")
        if not workspace_id or not commit_sha:
            raise ValueError("ci_status requires workspace_id and commit_sha")
        with db(tenant_id) as conn:
            row = conn.execute(
                "SELECT repository_id,state FROM workspaces WHERE id=? AND tenant_id=?",
                (workspace_id, tenant_id),
            ).fetchone()
            repo = conn.execute(
                "SELECT clone_url FROM repositories WHERE id=? AND tenant_id=? AND status='active'",
                (row[0], tenant_id),
            ).fetchone() if row else None
        if not row or row[1] != "ready" or not repo:
            raise ValueError("Workspace repository is unavailable for CI inspection.")
        evidence = GitHubCiInspector(str(repo[0])).inspect_commit(str(commit_sha))
        return build_result(
            operation="build",
            payload=payload,
            repository=str(row[0]),
            summary=f"GitHub CI status for {commit_sha[:12]} is {evidence['status']}.",
            evidence={"stage": "ci_status", "workspace_id": workspace_id, "ci": evidence},
        )

    @staticmethod
    def _evaluate_readiness_gate(payload: dict, tenant_id: str | None) -> dict:
        if not tenant_id:
            raise ValueError("Readiness evaluation requires a tenant context.")
        workspace_id = payload.get("workspace_id")
        if not workspace_id:
            raise ValueError("readiness_gate requires workspace_id")
        result = evaluate_production_readiness(
            quality_verified=bool(payload.get("quality_verified")),
            workspace_verified=bool(payload.get("workspace_verified")),
            ci_status=str(payload.get("ci_status", "failed")),
            change_set_synced=bool(payload.get("change_set_synced")),
            pull_request_open=bool(payload.get("pull_request_open")),
            deployment_verified=bool(payload.get("deployment_verified")),
            rollback_verified=bool(payload.get("rollback_verified")),
        )
        return build_result(
            operation="build",
            payload=payload,
            summary=f"Production readiness gate is {result['status']}.",
            evidence={"stage": "readiness_gate", "workspace_id": workspace_id, "readiness": result},
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
