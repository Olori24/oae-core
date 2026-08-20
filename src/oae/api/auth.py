import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Header, HTTPException, status

from oae.api.config import settings
from oae.api.db import db

_PBKDF2_ITERATIONS = 310_000
_HASH_PREFIX = "pbkdf2_sha256"
_KEY_PREFIX_LENGTH = 12
_MAX_API_KEY_LENGTH = 256


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_key(raw: str) -> str:
    """Hash an API key with a per-key random salt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", raw.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return "$".join(
        (
            _HASH_PREFIX,
            str(_PBKDF2_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode("ascii").rstrip("="),
            base64.urlsafe_b64encode(digest).decode("ascii").rstrip("="),
        )
    )


def _verify_hash(raw: str, stored: str) -> bool:
    parts = stored.split("$", 3)
    if len(parts) == 4 and parts[0] == _HASH_PREFIX:
        try:
            iterations = int(parts[1])
            salt = base64.urlsafe_b64decode(parts[2] + "===")
            expected = base64.urlsafe_b64decode(parts[3] + "===")
        except (TypeError, ValueError):
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", raw.encode("utf-8"), salt, iterations
        )
        return hmac.compare_digest(actual, expected)

    # Backward compatibility for keys issued by the previous HMAC scheme.
    if not settings.api_key_pepper:
        return False
    legacy = hmac.new(
        settings.api_key_pepper.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(legacy, stored)


def issue_api_key(tenant_id: str) -> str:
    return "oae_" + secrets.token_urlsafe(32)


def create_api_key(tenant_id: str) -> str:
    raw = issue_api_key(tenant_id)
    with db() as conn:
        conn.execute(
            "INSERT INTO api_keys(id, tenant_id, key_prefix, key_hash, created_at) VALUES(?,?,?,?,?)",
            (str(uuid4()), tenant_id, raw[:_KEY_PREFIX_LENGTH], hash_key(raw), _now()),
        )
    return raw


def require_tenant(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer API key required",
        )
    raw = authorization.removeprefix("Bearer ").strip()
    if not raw or len(raw) > _MAX_API_KEY_LENGTH:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    prefix = raw[:_KEY_PREFIX_LENGTH]
    with db() as conn:
        rows = conn.execute(
            "SELECT tenant_id,key_hash FROM api_keys WHERE revoked_at IS NULL AND key_prefix=?",
            (prefix,),
        ).fetchall()
        # Existing keys created before prefix indexing remain valid during migration.
        if not rows:
            rows = conn.execute(
                "SELECT tenant_id,key_hash FROM api_keys WHERE revoked_at IS NULL AND key_prefix IS NULL"
            ).fetchall()

    for row in rows:
        if _verify_hash(raw, str(row[1])):
            return str(row[0])
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
