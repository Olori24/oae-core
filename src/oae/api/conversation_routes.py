"""Conversation control surface for Mission 112.

The conversation layer is intentionally thin: it persists user intent and routes
authorized execution into the existing governed engineering job pipeline.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from oae.api.agent_runs import AgentRunRepository
from oae.api.auth import (
    TenantPrincipal,
    require_approver_principal,
    require_principal,
    require_requester_principal,
)
from oae.api.config import settings
from oae.api.db import db
from oae.api.durable_jobs import DurableJobRepository
from oae.api.worker_authorizations import WorkerAuthorizationRepository
from oae.core.engineering_planner import build_engineering_plan

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(default="New engineering session", min_length=1, max_length=160)
    repository_id: str | None = Field(default=None, max_length=120)
    workspace_id: str | None = Field(default=None, max_length=120)
    mode: Literal["ask", "plan", "execute"] = "ask"


class ConversationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    repository_id: str | None = Field(default=None, max_length=120)
    workspace_id: str | None = Field(default=None, max_length=120)
    mode: Literal["ask", "plan", "execute"] | None = None


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    content: str = Field(min_length=1, max_length=12000)
    mode: Literal["ask", "plan", "execute"] | None = None


class ExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    authorization_id: str = Field(min_length=1, max_length=120)

class PlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    repository_kind: Literal["python", "node", "typescript", "mixed", "unknown"] = "unknown"
    has_tests: bool = True
    has_linter: bool = True
    has_typecheck: bool = False
    test_runner: Literal["none", "vitest", "jest"] = "none"
    auto_context: bool = True


class AuthorizationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    expires_in_seconds: int = Field(default=3600, ge=60, le=7 * 24 * 60 * 60)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_tables() -> None:
    if settings.database_backend == "postgres":
        return
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, title TEXT NOT NULL,
            repository_id TEXT, workspace_id TEXT, mode TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS conversation_messages (
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, conversation_id TEXT NOT NULL,
            role TEXT NOT NULL, content TEXT NOT NULL, message_type TEXT NOT NULL DEFAULT 'text',
            metadata TEXT, created_at TEXT NOT NULL
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_tenant_updated ON conversations(tenant_id, updated_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conversation_messages_tenant_conversation ON conversation_messages(tenant_id, conversation_id, created_at)")


def _row(row) -> dict:
    return {
        "id": str(row[0]), "title": str(row[1]), "repository_id": row[2],
        "workspace_id": row[3], "mode": str(row[4]), "created_at": row[5], "updated_at": row[6],
    }


def _metadata(value) -> dict:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    return json.loads(value)


def _message(row) -> dict:
    return {
        "id": str(row[0]), "role": str(row[1]), "content": str(row[2]),
        "message_type": str(row[3]), "metadata": row[4] if isinstance(row[4], dict) else (json.loads(row[4]) if row[4] else {}),
        "created_at": row[5],
    }


def _get(conversation_id: str, tenant_id: str) -> dict:
    _ensure_tables()
    with db(tenant_id) as conn:
        row = conn.execute(
            "SELECT id,title,repository_id,workspace_id,mode,created_at,updated_at "
            "FROM conversations WHERE id=? AND tenant_id=?",
            (conversation_id, tenant_id),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Conversation not found")
        messages = conn.execute(
            "SELECT id,role,content,message_type,metadata,created_at "
            "FROM conversation_messages WHERE conversation_id=? AND tenant_id=? ORDER BY created_at ASC",
            (conversation_id, tenant_id),
        ).fetchall()
    result = _row(row)
    result["messages"] = [_message(item) for item in messages]
    return result


def _objective(content: str, mode: str, conversation: dict) -> dict:
    text = content.strip()
    lower = text.lower()
    if any(word in lower for word in ("fix", "bug", "error", "broken", "repair")):
        intent = "repair"
    elif any(word in lower for word in ("build", "add", "create", "implement")):
        intent = "build"
    elif any(word in lower for word in ("review", "audit", "security")):
        intent = "review"
    elif any(word in lower for word in ("test", "verify", "check")):
        intent = "verify"
    else:
        intent = "engineering_task"
    return {
        "intent": intent,
        "objective": text,
        "mode": mode,
        "repository_id": conversation.get("repository_id"),
        "workspace_id": conversation.get("workspace_id"),
    }


@router.post("", status_code=201)
def create_conversation(
    data: ConversationCreate,
    principal: TenantPrincipal = Depends(require_principal),
):
    principal = require_requester_principal(principal)
    _ensure_tables()
    now = _now()
    conversation_id = str(uuid4())
    with db(principal.tenant_id) as conn:
        conn.execute(
            "INSERT INTO conversations(id,tenant_id,title,repository_id,workspace_id,mode,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (conversation_id, principal.tenant_id, data.title, data.repository_id, data.workspace_id, data.mode, now, now),
        )
        conn.execute(
            "INSERT INTO conversation_messages(id,tenant_id,conversation_id,role,content,message_type,metadata,created_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (str(uuid4()), principal.tenant_id, conversation_id, "assistant",
             "I’m ready. Tell me what you want built, fixed, reviewed, or investigated.",
             "welcome", json.dumps({"type": "welcome"}), now),
        )
    return _get(conversation_id, principal.tenant_id)


@router.get("")
def list_conversations(principal: TenantPrincipal = Depends(require_principal)):
    _ensure_tables()
    with db(principal.tenant_id) as conn:
        rows = conn.execute(
            "SELECT id,title,repository_id,workspace_id,mode,created_at,updated_at "
            "FROM conversations WHERE tenant_id=? ORDER BY updated_at DESC LIMIT 100",
            (principal.tenant_id,),
        ).fetchall()
    return [_row(item) for item in rows]


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str, principal: TenantPrincipal = Depends(require_principal)):
    return _get(conversation_id, principal.tenant_id)


@router.patch("/{conversation_id}")
def update_conversation(
    conversation_id: str,
    data: ConversationUpdate,
    principal: TenantPrincipal = Depends(require_principal),
):
    principal = require_requester_principal(principal)
    current = _get(conversation_id, principal.tenant_id)
    now = _now()
    with db(principal.tenant_id) as conn:
        conn.execute(
            "UPDATE conversations SET repository_id=?,workspace_id=?,mode=?,updated_at=? "
            "WHERE id=? AND tenant_id=?",
            (
                data.repository_id if data.repository_id is not None else current["repository_id"],
                data.workspace_id if data.workspace_id is not None else current["workspace_id"],
                data.mode or current["mode"], now, conversation_id, principal.tenant_id,
            ),
        )
    return _get(conversation_id, principal.tenant_id)


@router.post("/{conversation_id}/messages")
def add_message(
    conversation_id: str,
    data: MessageCreate,
    principal: TenantPrincipal = Depends(require_principal),
):
    principal = require_requester_principal(principal)
    current = _get(conversation_id, principal.tenant_id)
    mode = data.mode or current["mode"]
    objective = _objective(data.content, mode, current)
    now = _now()
    with db(principal.tenant_id) as conn:
        conn.execute(
            "INSERT INTO conversation_messages(id,tenant_id,conversation_id,role,content,message_type,metadata,created_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (str(uuid4()), principal.tenant_id, conversation_id, "user", data.content, "text",
             json.dumps({"objective": objective}), now),
        )
        title = current["title"]
        if title == "New engineering session":
            title = data.content[:80]
        conn.execute(
            "UPDATE conversations SET mode=?,title=?,updated_at=? WHERE id=? AND tenant_id=?",
            (mode, title, now, conversation_id, principal.tenant_id),
        )
        conn.execute(
            "INSERT INTO conversation_messages(id,tenant_id,conversation_id,role,content,message_type,metadata,created_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (str(uuid4()), principal.tenant_id, conversation_id, "assistant",
             f"I understand this as a {objective['intent'].replace('_', ' ')} objective. "
             f"Mode: {mode.upper()}. Consequential changes remain behind OAE’s governance gates.",
             "engineering_ack", json.dumps(objective), _now()),
        )
    return _get(conversation_id, principal.tenant_id)


@router.post("/{conversation_id}/plan")
def create_plan(conversation_id: str, data: PlanRequest, principal: TenantPrincipal = Depends(require_principal)):
    principal = require_requester_principal(principal)
    _get(conversation_id, principal.tenant_id)
    with db(principal.tenant_id) as conn:
        row = conn.execute(
            "SELECT content,metadata FROM conversation_messages WHERE conversation_id=? AND tenant_id=? AND role='user' ORDER BY created_at DESC LIMIT 1",
            (conversation_id, principal.tenant_id),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=422, detail="No engineering objective found.")
    metadata = _metadata(row[1])
    objective = metadata.get("objective", {}).get("objective") or row[0]
    current = _get(conversation_id, principal.tenant_id)
    repository_context: dict[str, object] = {"selected": False}
    repository_kind = data.repository_kind
    has_tests = data.has_tests
    has_linter = data.has_linter
    has_typecheck = data.has_typecheck
    test_runner = data.test_runner
    if data.auto_context and current.get("repository_id"):
        with db(principal.tenant_id) as conn:
            repo = conn.execute(
                "SELECT id,provider,external_id,default_branch,status FROM repositories "
                "WHERE id=? AND tenant_id=? AND deleted_at IS NULL",
                (current["repository_id"], principal.tenant_id),
            ).fetchone()
        if repo:
            repository_context = {
                "selected": True,
                "repository_id": str(repo[0]),
                "provider": str(repo[1]),
                "external_id": str(repo[2]),
                "default_branch": str(repo[3]),
                "status": str(repo[4]),
            }
    plan = build_engineering_plan(
        objective=str(objective),
        repository_kind=repository_kind,
        has_tests=has_tests,
        has_linter=has_linter,
        has_typecheck=has_typecheck,
        test_runner=test_runner,
        security_required=True,
    ).to_dict()
    now = _now()
    with db(principal.tenant_id) as conn:
        conn.execute(
            "INSERT INTO conversation_messages(id,tenant_id,conversation_id,role,content,message_type,metadata,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (str(uuid4()), principal.tenant_id, conversation_id, "assistant",
             "Engineering plan generated. No repository mutation has been performed.",
             "plan", json.dumps({"plan": plan}, separators=(",", ":")), now),
        )
        conn.execute("UPDATE conversations SET updated_at=? WHERE id=? AND tenant_id=?", (now, conversation_id, principal.tenant_id))
    return {"conversation_id": conversation_id, "plan": plan, "repository_context": repository_context, "status": "planned"}


@router.post("/{conversation_id}/authorization", status_code=201)
def request_execution_authorization(conversation_id: str, data: AuthorizationCreate, principal: TenantPrincipal = Depends(require_principal)):
    principal = require_requester_principal(principal)
    current = _get(conversation_id, principal.tenant_id)
    if current["mode"] != "execute":
        raise HTTPException(status_code=409, detail="Conversation must be in EXECUTE mode.")
    if not current.get("workspace_id"):
        raise HTTPException(status_code=422, detail="Select a ready engineering workspace before execution.")
    with db(principal.tenant_id) as conn:
        row = conn.execute(
            "SELECT content FROM conversation_messages WHERE conversation_id=? AND tenant_id=? AND role='user' ORDER BY created_at DESC LIMIT 1",
            (conversation_id, principal.tenant_id),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=422, detail="No engineering objective found.")
    authorization = WorkerAuthorizationRepository().request(
        tenant_id=principal.tenant_id,
        operation="build",
        scope={
            "conversation_id": conversation_id,
            "workspace_id": str(current["workspace_id"]),
            "objective_sha256": hashlib.sha256(str(row[0]).encode("utf-8")).hexdigest(),
        },
        requester=principal.principal_id,
        expires_in_seconds=data.expires_in_seconds,
    )
    return {"authorization_id": authorization.id, "status": authorization.status, "operation": authorization.operation,
            "scope": authorization.scope, "expires_at": authorization.expires_at.isoformat()}


@router.get("/{conversation_id}/authorization")
def get_execution_authorization(conversation_id: str, principal: TenantPrincipal = Depends(require_principal)):
    _get(conversation_id, principal.tenant_id)
    with db(principal.tenant_id) as conn:
        rows = conn.execute(
            "SELECT id,scope FROM worker_authorizations WHERE tenant_id=? AND operation='build' ORDER BY requested_at DESC LIMIT 20",
            (principal.tenant_id,),
        ).fetchall()
    authorization_id = None
    for candidate in rows:
        scope = candidate[1]
        scope = json.loads(scope) if isinstance(scope, str) else scope
        if isinstance(scope, dict) and scope.get("conversation_id") == conversation_id:
            authorization_id = str(candidate[0])
            break
    if not authorization_id:
        return {"authorization": None}
    record = WorkerAuthorizationRepository().get(tenant_id=principal.tenant_id, authorization_id=authorization_id)
    if not record:
        return {"authorization": None}
    return {"authorization": {"id": record.id, "status": record.status, "operation": record.operation,
                              "scope": record.scope, "expires_at": record.expires_at.isoformat(),
                              "decided_at": record.decided_at.isoformat() if record.decided_at else None}}


@router.post("/{conversation_id}/authorization/{authorization_id}/approve")
def approve_execution_authorization(
    conversation_id: str,
    authorization_id: str,
    principal: TenantPrincipal = Depends(require_principal),
):
    principal = require_approver_principal(principal)
    current = _get(conversation_id, principal.tenant_id)
    record = WorkerAuthorizationRepository().get(
        tenant_id=principal.tenant_id, authorization_id=authorization_id
    )
    if not record or record.scope.get("conversation_id") != conversation_id:
        raise HTTPException(status_code=404, detail="Authorization not found for this conversation.")
    if record.scope.get("workspace_id") != str(current.get("workspace_id")):
        raise HTTPException(status_code=403, detail="Authorization scope does not match this workspace.")
    WorkerAuthorizationRepository().approve(
        tenant_id=principal.tenant_id, authorization_id=authorization_id,
        approver=principal.principal_id, approver_role=principal.role,
        decision_reason_redacted="Approved from OAE engineering control surface.",
    )
    return {"authorization_id": authorization_id, "status": "approved"}


@router.get("/{conversation_id}/runs/{run_id}")
def get_engineering_run(conversation_id: str, run_id: str, principal: TenantPrincipal = Depends(require_principal)):
    current = _get(conversation_id, principal.tenant_id)
    record = AgentRunRepository().get(tenant_id=principal.tenant_id, run_id=run_id)
    if record.workspace_id != current.get("workspace_id"):
        raise HTTPException(status_code=404, detail="Engineering run not found.")
    return {"id": record.id, "status": record.state.status, "workspace_id": record.workspace_id,
            "authorization_id": record.authorization_id, "completed_steps": list(record.state.completed_steps),
            "failed_step": record.state.failed_step, "repair_count": record.state.repair_count,
            "evidence": list(record.state.evidence), "plan": record.state.plan,
            "created_at": record.created_at, "updated_at": record.updated_at}


@router.post("/{conversation_id}/execute")
def execute_conversation(
    conversation_id: str,
    data: ExecuteRequest,
    principal: TenantPrincipal = Depends(require_principal),
):
    principal = require_requester_principal(principal)
    current = _get(conversation_id, principal.tenant_id)
    if current["mode"] != "execute":
        raise HTTPException(status_code=409, detail="Conversation must be in EXECUTE mode.")
    if not current.get("workspace_id"):
        raise HTTPException(status_code=422, detail="Select a ready engineering workspace before execution.")
    if settings.database_backend != "postgres" or not settings.durable_jobs_enabled:
        raise HTTPException(status_code=503, detail="Governed execution requires PostgreSQL durable jobs.")
    if not WorkerAuthorizationRepository().is_approved_for_execution(
        tenant_id=principal.tenant_id, authorization_id=data.authorization_id, operation="build"
    ):
        raise HTTPException(status_code=403, detail="An active governed worker authorization is required.")
    with db(principal.tenant_id) as conn:
        row = conn.execute(
            "SELECT content,metadata FROM conversation_messages "
            "WHERE conversation_id=? AND tenant_id=? AND role='user' ORDER BY created_at DESC LIMIT 1",
            (conversation_id, principal.tenant_id),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=422, detail="No engineering objective found.")
    metadata = json.loads(row[1] or "{}")
    objective = metadata.get("objective", {}).get("objective") or row[0]
    authorization = WorkerAuthorizationRepository().get(
        tenant_id=principal.tenant_id, authorization_id=data.authorization_id
    )
    if not authorization or authorization.operation != "build" or authorization.status != "approved":
        raise HTTPException(status_code=403, detail="An active approved build authorization is required.")
    if authorization.scope.get("conversation_id") != conversation_id:
        raise HTTPException(status_code=403, detail="Authorization scope does not match this conversation.")
    plan = build_engineering_plan(
        objective=str(objective), repository_kind="unknown", has_tests=True, has_linter=True,
        has_typecheck=False, test_runner="none", security_required=True,
    ).to_dict()
    key = hashlib.sha256(objective.encode("utf-8")).hexdigest()[:24]
    run = AgentRunRepository().start(
        tenant_id=principal.tenant_id, workspace_id=str(current["workspace_id"]), plan=plan,
        idempotency_key=f"conversation-run:{conversation_id}:{key}", correlation_id=conversation_id,
        max_repairs=2, authorization_id=data.authorization_id,
    )
    if run.state.status == "running":
        DurableJobRepository().enqueue(
            tenant_id=principal.tenant_id, operation="build",
            payload={"stage": "agent_tick", "run_id": run.id},
            authorization_id=data.authorization_id,
            idempotency_key=f"conversation-agent-tick:{run.id}:0:0", priority=90,
        )
        # Do not leave the run waiting for a nonexistent always-on worker.
        # Serverless execution drains a bounded number of authorized steps now;
        # the durable queue remains the recovery mechanism.
        processed_jobs = JobRunner().drain_authorized_queue(
            worker_name=f"conversation-{conversation_id[:12]}",
            max_jobs=8,
        )
    else:
        processed_jobs = 0
    return {"run_id": run.id, "status": run.state.status, "objective": objective,
            "processed_jobs": processed_jobs,
            "authorization_id": data.authorization_id, "plan": plan}


@router.post("/{conversation_id}/attachments")
async def upload_attachment(
    conversation_id: str,
    file: UploadFile = File(...),
    principal: TenantPrincipal = Depends(require_principal),
):
    principal = require_requester_principal(principal)
    _get(conversation_id, principal.tenant_id)
    allowed = {
        "application/pdf", "text/plain", "text/markdown",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/png", "image/jpeg", "image/webp", "video/mp4",
        "audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4",
    }
    content_type = file.content_type or "application/octet-stream"
    if content_type not in allowed:
        raise HTTPException(status_code=415, detail="Unsupported attachment type.")
    data = await file.read(12 * 1024 * 1024 + 1)
    if len(data) > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Attachment exceeds the 12 MB limit.")
    metadata = {
        "filename": file.filename or "attachment",
        "content_type": content_type,
        "size_bytes": len(data),
        "ingestion_status": "accepted",
    }
    with db(principal.tenant_id) as conn:
        conn.execute(
            "INSERT INTO conversation_messages(id,tenant_id,conversation_id,role,content,message_type,metadata,created_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (str(uuid4()), principal.tenant_id, conversation_id, "user",
             f"Attached {metadata['filename']}", "attachment", json.dumps(metadata), _now()),
        )
        conn.execute(
            "UPDATE conversations SET updated_at=? WHERE id=? AND tenant_id=?",
            (_now(), conversation_id, principal.tenant_id),
        )
    return _get(conversation_id, principal.tenant_id)
