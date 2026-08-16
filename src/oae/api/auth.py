import hashlib
import hmac
import secrets
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, status

from oae.api.config import settings
from oae.api.db import db


def hash_key(raw: str) -> str:
    return hmac.new(
        settings.api_key_pepper.encode(), raw.encode(), hashlib.sha256
    ).hexdigest()


def issue_api_key(tenant_id: str) -> str:
    return "oae_" + secrets.token_urlsafe(32)


def create_api_key(tenant_id: str) -> str:
    raw = issue_api_key(tenant_id)
    with db() as conn:
        conn.execute(
            "INSERT INTO api_keys(id, tenant_id, key_hash, created_at) VALUES(?,?,?,datetime('now'))",
            (str(uuid4()), tenant_id, hash_key(raw)),
        )
    return raw


def require_tenant(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer API key required")
    raw = authorization.removeprefix("Bearer ").strip()
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    with db() as conn:
        row = conn.execute(
            "SELECT tenant_id FROM api_keys WHERE key_hash=? AND revoked_at IS NULL",
            (hash_key(raw),),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return str(row[0])
