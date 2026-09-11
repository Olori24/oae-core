import base64
import hashlib
import hmac
import secrets
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Header, HTTPException, status

from oae.api.config import settings
from oae.api.db import db

_PBKDF2_ITERATIONS = 310_000
_HASH_PREFIX = "pbkdf2_sha256"
_KEY_PREFIX_LENGTH = 12
_MAX_API_KEY_LENGTH = 256
_PRINCIPAL_ROLES = frozenset({"owner", "operator", "approver", "viewer"})
_REQUESTER_ROLES = frozenset({"owner", "operator"})
_APPROVER_ROLES = frozenset({"owner", "approver"})
_AUTH_CACHE_LOCK = threading.Lock()
_AUTH_CACHE: OrderedDict[str, tuple[float, "TenantPrincipal"]] = OrderedDict()
_AUTH_CACHE_HITS = 0
_AUTH_CACHE_MISSES = 0


@dataclass(frozen=True)
class TenantPrincipal:
    tenant_id: str
    key_id: str
    principal_id: str
    role: str


@dataclass(frozen=True)
class IssuedApiKey:
    id: str
    tenant_id: str
    principal_id: str
    principal_role: str
    api_key: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_PROCESS_CACHE_SECRET = secrets.token_bytes(32)


def _cache_key(raw: str) -> str:
    """Derive a non-reversible cache key; never retain the plaintext API key."""
    secret = settings.api_key_pepper.encode("utf-8") or _PROCESS_CACHE_SECRET
    return hmac.new(secret, raw.encode("utf-8"), hashlib.sha256).hexdigest()


def _cache_get(raw: str) -> TenantPrincipal | None:
    global _AUTH_CACHE_HITS, _AUTH_CACHE_MISSES
    key = _cache_key(raw)
    now = time.monotonic()
    with _AUTH_CACHE_LOCK:
        item = _AUTH_CACHE.get(key)
        if item is None:
            _AUTH_CACHE_MISSES += 1
            return None
        expires_at, principal = item
        if expires_at <= now:
            _AUTH_CACHE.pop(key, None)
            _AUTH_CACHE_MISSES += 1
            return None
        _AUTH_CACHE.move_to_end(key)
        _AUTH_CACHE_HITS += 1
        return principal


def _cache_put(raw: str, principal: TenantPrincipal) -> None:
    key = _cache_key(raw)
    with _AUTH_CACHE_LOCK:
        _AUTH_CACHE[key] = (time.monotonic() + settings.auth_cache_ttl_seconds, principal)
        _AUTH_CACHE.move_to_end(key)
        while len(_AUTH_CACHE) > settings.auth_cache_max_entries:
            _AUTH_CACHE.popitem(last=False)


def _cache_invalidate_key(key_id: str) -> None:
    with _AUTH_CACHE_LOCK:
        stale = [
            cache_key
            for cache_key, (_, principal) in _AUTH_CACHE.items()
            if principal.key_id == key_id
        ]
        for cache_key in stale:
            _AUTH_CACHE.pop(cache_key, None)


def auth_cache_metrics() -> dict[str, int | float]:
    with _AUTH_CACHE_LOCK:
        total = _AUTH_CACHE_HITS + _AUTH_CACHE_MISSES
        return {
            "entries": len(_AUTH_CACHE),
            "hits": _AUTH_CACHE_HITS,
            "misses": _AUTH_CACHE_MISSES,
            "hit_ratio": (_AUTH_CACHE_HITS / total) if total else 0.0,
        }


def hash_key(raw: str) -> str:
    """Hash an API key with a per-key random salt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", raw.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
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
        actual = hashlib.pbkdf2_hmac("sha256", raw.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)

    if not settings.api_key_pepper:
        return False
    legacy = hmac.new(
        settings.api_key_pepper.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(legacy, stored)


def issue_api_key(tenant_id: str) -> str:
    return "oae_" + secrets.token_urlsafe(32)


def create_api_key(
    tenant_id: str,
    *,
    principal_id: str | None = None,
    principal_role: str = "owner",
) -> str:
    return create_principal_api_key(
        tenant_id,
        principal_id=principal_id,
        principal_role=principal_role,
    ).api_key


def create_principal_api_key(
    tenant_id: str,
    *,
    principal_id: str | None = None,
    principal_role: str,
) -> IssuedApiKey:
    if principal_role not in _PRINCIPAL_ROLES:
        raise ValueError("Unsupported API key principal role")
    raw = issue_api_key(tenant_id)
    key_id = str(uuid4())
    resolved_principal_id = principal_id or key_id
    with db() as conn:
        conn.execute(
            """
            INSERT INTO api_keys(
                id,tenant_id,key_prefix,key_hash,principal_id,principal_role,created_at
            ) VALUES(?,?,?,?,?,?,?)
            """,
            (
                key_id,
                tenant_id,
                raw[:_KEY_PREFIX_LENGTH],
                hash_key(raw),
                resolved_principal_id,
                principal_role,
                _now(),
            ),
        )
    return IssuedApiKey(
        id=key_id,
        tenant_id=tenant_id,
        principal_id=resolved_principal_id,
        principal_role=principal_role,
        api_key=raw,
    )


def revoke_principal_api_key(*, tenant_id: str, key_id: str) -> bool:
    with db() as conn:
        changed = conn.execute(
            "UPDATE api_keys SET revoked_at=? WHERE id=? AND tenant_id=? AND revoked_at IS NULL",
            (_now(), key_id, tenant_id),
        ).rowcount
    if changed == 1:
        _cache_invalidate_key(key_id)
    return changed == 1


def require_principal(authorization: str | None = Header(default=None)) -> TenantPrincipal:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer API key required",
        )
    raw = authorization.removeprefix("Bearer ").strip()
    if not raw or len(raw) > _MAX_API_KEY_LENGTH:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    cached = _cache_get(raw)
    if cached is not None:
        return cached

    prefix = raw[:_KEY_PREFIX_LENGTH]
    with db() as conn:
        rows = conn.execute(
            """
            SELECT id,tenant_id,key_hash,COALESCE(principal_id,id),COALESCE(principal_role,'owner')
            FROM api_keys WHERE revoked_at IS NULL AND key_prefix=?
            """,
            (prefix,),
        ).fetchall()
        if not rows:
            rows = conn.execute(
                """
                SELECT id,tenant_id,key_hash,COALESCE(principal_id,id),COALESCE(principal_role,'owner')
                FROM api_keys WHERE revoked_at IS NULL AND key_prefix IS NULL
                """
            ).fetchall()

    for row in rows:
        if _verify_hash(raw, str(row[2])):
            role = str(row[4])
            if role not in _PRINCIPAL_ROLES:
                break
            principal = TenantPrincipal(
                key_id=str(row[0]),
                tenant_id=str(row[1]),
                principal_id=str(row[3]),
                role=role,
            )
            _cache_put(raw, principal)
            return principal
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def require_tenant(authorization: str | None = Header(default=None)) -> str:
    return require_principal(authorization).tenant_id


def require_requester_principal(principal: TenantPrincipal) -> TenantPrincipal:
    if principal.role not in _REQUESTER_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requester role required")
    return principal


def require_approver_principal(principal: TenantPrincipal) -> TenantPrincipal:
    if principal.role not in _APPROVER_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Approver role required")
    return principal


def require_owner_principal(principal: TenantPrincipal) -> TenantPrincipal:
    if principal.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner role required")
    return principal
