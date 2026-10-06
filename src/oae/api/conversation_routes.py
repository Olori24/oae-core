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

from oae.api.auth import TenantPrincipal, require_principal, require_requester_principal
from oae.api.config import settings
from oae.api.db import db
from oae.api.durable_jobs import DurableJobRepository
from oae.api.worker_authorizations import WorkerAuthorizationRepository

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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_tables() -> None:
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


def _message(row) -> dict:
    return {
        "id": str(row[0]), "role": str(row[1]), "content": str(row[2]),
        "message_type": str(row[3]), "metadata": json.loads(row[4]) if row[4] else {},
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
    key = hashlib.sha256(objective.encode("utf-8")).hexdigest()[:24]
    job = DurableJobRepository().enqueue(
        tenant_id=principal.tenant_id,
        operation="build",
        payload={"stage": "coding_proposal", "workspace_id": current["workspace_id"], "objective": objective},
        authorization_id=data.authorization_id,
        idempotency_key=f"conversation:{conversation_id}:{key}",
        priority=100,
    )
    return {"job_id": job.id, "status": job.status, "objective": objective}


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
