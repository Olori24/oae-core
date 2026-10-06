"""PostgreSQL persistence for bounded autonomous engineering run state."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from oae.api.db import db
from oae.core.agent_runtime import AgentRunState, record_step_result, start_agent_run


@dataclass(frozen=True)
class AgentRunRecord:
    id: str
    tenant_id: str
    workspace_id: str
    state: AgentRunState
    idempotency_key: str | None
    correlation_id: str | None
    authorization_id: str | None
    active_step_id: str | None
    active_token: str | None
    lease_until: str | None
    created_at: str
    updated_at: str


class AgentRunRepository:
    def start(
        self,
        *,
        tenant_id: str,
        workspace_id: str,
        plan: dict[str, Any],
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
        max_repairs: int = 2,
        authorization_id: str | None = None,
    ) -> AgentRunRecord:
        run_id = str(uuid4())
        state = start_agent_run(run_id=run_id, plan=plan, max_repairs=max_repairs)
        now = datetime.now(timezone.utc)
        with db(tenant_id) as conn:
            conn.execute(
                """
                INSERT INTO engineering_agent_runs(
                    id,tenant_id,workspace_id,plan,status,completed_steps,failed_step,
                    repair_count,evidence,idempotency_key,correlation_id,authorization_id,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(tenant_id,idempotency_key) DO NOTHING
                """,
                (
                    run_id,
                    tenant_id,
                    workspace_id,
                    json.dumps(state.plan, separators=(",", ":"), sort_keys=True),
                    state.status,
                    json.dumps(list(state.completed_steps)),
                    state.failed_step,
                    state.repair_count,
                    json.dumps(list(state.evidence), separators=(",", ":"), sort_keys=True),
                    idempotency_key,
                    correlation_id,
                    authorization_id,
                    now,
                    now,
                ),
            )
            if idempotency_key:
                existing = conn.execute(
                    "SELECT id FROM engineering_agent_runs WHERE tenant_id=? AND idempotency_key=?",
                    (tenant_id, idempotency_key),
                ).fetchone()
                if existing:
                    return self.get(tenant_id=tenant_id, run_id=str(existing[0]))
        return self.get(tenant_id=tenant_id, run_id=run_id)

    def get(self, *, tenant_id: str, run_id: str) -> AgentRunRecord:
        with db(tenant_id) as conn:
            row = conn.execute(
                """
                SELECT id,tenant_id,workspace_id,plan,status,completed_steps,failed_step,
                       repair_count,evidence,idempotency_key,correlation_id,authorization_id,active_step_id,active_token,lease_until,created_at,updated_at
                FROM engineering_agent_runs
                WHERE id=? AND tenant_id=?
                """,
                (run_id, tenant_id),
            ).fetchone()
        if not row:
            raise ValueError("Agent run not found for tenant.")
        state = AgentRunState(
            run_id=str(row[0]),
            status=str(row[4]),
            plan=json.loads(row[3]),
            completed_steps=tuple(json.loads(row[5])),
            failed_step=row[6],
            repair_count=int(row[7]),
            evidence=tuple(json.loads(row[8])),
        )
        return AgentRunRecord(
            id=str(row[0]),
            tenant_id=str(row[1]),
            workspace_id=str(row[2]),
            state=state,
            idempotency_key=row[9],
            correlation_id=row[10],
            authorization_id=row[11],
            active_step_id=row[12],
            active_token=row[13],
            lease_until=str(row[14]) if row[14] else None,
            created_at=str(row[15]),
            updated_at=str(row[16]),
        )

    def claim_next_action(self, *, tenant_id: str, run_id: str, lease_seconds: int = 120) -> tuple[AgentRunRecord, str, dict[str, Any]] | None:
        now = datetime.now(timezone.utc)
        lease_until = now + timedelta(seconds=max(30, min(300, lease_seconds)))
        token = str(uuid4())
        with db(tenant_id) as conn:
            row = conn.execute(
                "SELECT id,workspace_id,plan,status,completed_steps,failed_step,repair_count,evidence,idempotency_key,correlation_id,authorization_id,active_step_id,active_token,lease_until,created_at,updated_at FROM engineering_agent_runs WHERE id=? AND tenant_id=? FOR UPDATE",
                (run_id, tenant_id),
            ).fetchone()
            if not row:
                raise ValueError("Agent run not found for tenant.")
            if row[12] and row[13]:
                existing_until = datetime.fromisoformat(str(row[14])) if row[14] else now
                if existing_until > now:
                    return None
            state = AgentRunState(run_id=str(row[0]), status=str(row[3]), plan=json.loads(row[2]), completed_steps=tuple(json.loads(row[4])), failed_step=row[5], repair_count=int(row[6]), evidence=tuple(json.loads(row[7])))
            decision = state.next_decision()
            if decision.status != "ready" or not decision.step_id:
                return None
            conn.execute("UPDATE engineering_agent_runs SET active_step_id=?,active_token=?,lease_until=?,updated_at=? WHERE id=? AND tenant_id=?", (decision.step_id, token, lease_until, now, run_id, tenant_id))
        record = self.get(tenant_id=tenant_id, run_id=run_id)
        return record, token, decision.to_dict()
    def record_result(
        self,
        *,
        tenant_id: str,
        run_id: str,
        step_id: str,
        success: bool,
        evidence: dict[str, Any] | None = None,
        action_token: str | None = None,
    ) -> AgentRunRecord:
        with db(tenant_id) as conn:
            row = conn.execute(
                """
                SELECT id,workspace_id,plan,status,completed_steps,failed_step,
                       repair_count,evidence,idempotency_key,correlation_id,authorization_id,active_step_id,active_token,lease_until,created_at,updated_at
                FROM engineering_agent_runs
                WHERE id=? AND tenant_id=?
                FOR UPDATE
                """,
                (run_id, tenant_id),
            ).fetchone()
            if not row:
                raise ValueError("Agent run not found for tenant.")
            if row[12] and row[12] != action_token:
                raise ValueError("Agent action lease is missing or stale.")
            current = AgentRunState(
                run_id=str(row[0]),
                status=str(row[3]),
                plan=json.loads(row[2]),
                completed_steps=tuple(json.loads(row[4])),
                failed_step=row[5],
                repair_count=int(row[6]),
                evidence=tuple(json.loads(row[7])),
            )
            updated = record_step_result(
                current,
                step_id=step_id,
                success=success,
                evidence=evidence,
            )
            now = datetime.now(timezone.utc)
            conn.execute(
                """
                UPDATE engineering_agent_runs
                SET status=?,completed_steps=?,failed_step=?,repair_count=?,evidence=?,active_step_id=NULL,active_token=NULL,lease_until=NULL,updated_at=?
                WHERE id=? AND tenant_id=?
                """,
                (
                    updated.status,
                    json.dumps(list(updated.completed_steps)),
                    updated.failed_step,
                    updated.repair_count,
                    json.dumps(list(updated.evidence), separators=(",", ":"), sort_keys=True),
                    now,
                    run_id,
                    tenant_id,
                ),
            )
        return self.get(tenant_id=tenant_id, run_id=run_id)
