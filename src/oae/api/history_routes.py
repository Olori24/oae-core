"""User-owned conversation history controls and bounded message pagination."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from oae.api.auth import TenantPrincipal, require_principal, require_requester_principal
from oae.api.config import settings
from oae.api.db import db

router = APIRouter(prefix="/v1/history", tags=["conversation history"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_tables() -> None:
    if settings.database_backend == "postgres":
        return
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS oae_conversation_state (
            tenant_id TEXT NOT NULL, conversation_id TEXT NOT NULL,
            archived_at TEXT, deleted_at TEXT, updated_at TEXT NOT NULL,
            PRIMARY KEY(tenant_id,conversation_id))""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_oae_conversation_state_archive ON oae_conversation_state(tenant_id,archived_at,updated_at DESC)")


class RenameConversation(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=160)


def _require_conversation(conn, tenant_id: str, conversation_id: str):
    row = conn.execute("SELECT id,title,repository_id,workspace_id,mode,created_at,updated_at FROM conversations WHERE id=? AND tenant_id=?", (conversation_id,tenant_id)).fetchone()
    if not row:
        raise HTTPException(status_code=404,detail="Conversation not found")
    return row


@router.get("/conversations")
def list_history(q: str | None = Query(default=None,max_length=300), include_archived: bool=False, limit: int=Query(default=50,ge=1,le=100), principal: TenantPrincipal=Depends(require_principal)):
    _ensure_tables()
    with db(principal.tenant_id) as conn:
        sql = """SELECT c.id,c.title,c.repository_id,c.workspace_id,c.mode,c.created_at,c.updated_at,
                 s.archived_at,(SELECT m.content FROM conversation_messages m WHERE m.tenant_id=c.tenant_id AND m.conversation_id=c.id ORDER BY m.created_at DESC LIMIT 1) AS last_message
                 FROM conversations c LEFT JOIN oae_conversation_state s ON s.tenant_id=c.tenant_id AND s.conversation_id=c.id
                 WHERE c.tenant_id=? AND s.deleted_at IS NULL"""
        params: list[Any]=[principal.tenant_id]
        if not include_archived:
            sql += " AND s.archived_at IS NULL"
        if q:
            sql += " AND (lower(c.title) LIKE ? OR EXISTS (SELECT 1 FROM conversation_messages m WHERE m.tenant_id=c.tenant_id AND m.conversation_id=c.id AND lower(m.content) LIKE ?))"
            params.extend(["%"+q.lower()+"%","%"+q.lower()+"%"])
        sql += " ORDER BY c.updated_at DESC LIMIT ?"
        params.append(limit)
        rows=conn.execute(sql,tuple(params)).fetchall()
    return [{"id":r[0],"title":r[1],"repository_id":r[2],"workspace_id":r[3],"mode":r[4],"created_at":r[5],"updated_at":r[6],"archived_at":r[7],"last_message":r[8]} for r in rows]


@router.patch("/conversations/{conversation_id}")
def rename_history(conversation_id: str,data: RenameConversation,principal: TenantPrincipal=Depends(require_principal)):
    principal=require_requester_principal(principal)
    _ensure_tables()
    now=_now()
    with db(principal.tenant_id) as conn:
        _require_conversation(conn,principal.tenant_id,conversation_id)
        conn.execute("UPDATE conversations SET title=?,updated_at=? WHERE id=? AND tenant_id=?",(data.title,now,conversation_id,principal.tenant_id))
        conn.execute("INSERT INTO oae_conversation_state(tenant_id,conversation_id,updated_at) VALUES(?,?,?) ON CONFLICT(tenant_id,conversation_id) DO UPDATE SET updated_at=excluded.updated_at",(principal.tenant_id,conversation_id,now))
    return {"id":conversation_id,"title":data.title,"updated_at":now}


@router.post("/conversations/{conversation_id}/archive")
def archive_history(conversation_id: str,archived: bool=True,principal: TenantPrincipal=Depends(require_principal)):
    principal=require_requester_principal(principal)
    _ensure_tables()
    now=_now()
    with db(principal.tenant_id) as conn:
        _require_conversation(conn,principal.tenant_id,conversation_id)
        conn.execute("INSERT INTO oae_conversation_state(tenant_id,conversation_id,archived_at,updated_at) VALUES(?,?,?,?) ON CONFLICT(tenant_id,conversation_id) DO UPDATE SET archived_at=excluded.archived_at,updated_at=excluded.updated_at",
                     (principal.tenant_id,conversation_id,now if archived else None,now))
    return {"id":conversation_id,"archived":archived,"updated_at":now}


@router.delete("/conversations/{conversation_id}",status_code=204)
def delete_history(conversation_id: str,principal: TenantPrincipal=Depends(require_principal)):
    principal=require_requester_principal(principal)
    _ensure_tables()
    with db(principal.tenant_id) as conn:
        _require_conversation(conn,principal.tenant_id,conversation_id)
        # Conversation-derived memory is not silently deleted: provenance remains visible
        # so the user can review and delete those memory records independently.
        conn.execute("DELETE FROM conversation_messages WHERE tenant_id=? AND conversation_id=?",(principal.tenant_id,conversation_id))
        conn.execute("DELETE FROM conversations WHERE tenant_id=? AND id=?",(principal.tenant_id,conversation_id))
        # Hard deletion removes the conversation and its messages. No tombstone is kept here.


@router.get("/conversations/{conversation_id}/messages")
def paginate_history(conversation_id: str,limit: int=Query(default=50,ge=1,le=100),before: str|None=None,principal: TenantPrincipal=Depends(require_principal)):
    _ensure_tables()
    with db(principal.tenant_id) as conn:
        _require_conversation(conn,principal.tenant_id,conversation_id)
        sql="SELECT id,role,content,message_type,metadata,created_at FROM conversation_messages WHERE tenant_id=? AND conversation_id=?"
        params: list[Any]=[principal.tenant_id,conversation_id]
        if before:
            # Cursor format is the stable pair created_at|id; opaque base64 cursors can be added
            # without changing ordering semantics.
            if "|" not in before or len(before)>220:
                raise HTTPException(status_code=422,detail="Invalid message cursor")
            stamp,message_id=before.rsplit("|",1)
            sql += " AND (created_at<? OR (created_at=? AND id<?))"
            params.extend([stamp,stamp,message_id])
        sql += " ORDER BY created_at DESC,id DESC LIMIT ?"
        params.append(limit+1)
        rows=conn.execute(sql,tuple(params)).fetchall()
    has_more=len(rows)>limit
    rows=rows[:limit]
    rows.reverse()
    messages=[]
    import json
    for r in rows:
        metadata=r[4] if isinstance(r[4],dict) else (json.loads(r[4]) if r[4] else {})
        messages.append({"id":r[0],"role":r[1],"content":r[2],"message_type":r[3],"metadata":metadata,"created_at":r[5]})
    next_before=f"{rows[0][5]}|{rows[0][0]}" if has_more and rows else None
    return {"conversation_id":conversation_id,"messages":messages,"has_more":has_more,"next_before":next_before}
