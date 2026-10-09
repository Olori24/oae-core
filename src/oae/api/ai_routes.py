"""Model-backed conversational boundary for OAE.

This endpoint only reasons and returns text. Repository mutation remains in the
governed engineering pipeline and requires the existing authorization gates.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from oae.api.auth import TenantPrincipal, require_principal, require_requester_principal
from oae.core.ai_gateway import AIGatewayUnavailable, generate_engineering_response, model_available

router = APIRouter(prefix="/v1/ai", tags=["ai"])


class AIMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    role: Literal["user", "assistant"] = "user"
    content: str = Field(min_length=1, max_length=12000)


class AIRespondRequest(BaseModel):
    """Conversation request with explicit response-language control."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    messages: list[AIMessage] = Field(min_length=1, max_length=24)
    system: str | None = Field(default=None, max_length=12000)
    model: str | None = Field(default=None, max_length=120)
    language: Literal["en", "it", "de", "fr", "es", "pt", "ar", "yo", "ha", "ig"] = "en"


@router.get("/status")
def ai_status(principal: TenantPrincipal = Depends(require_principal)):
    require_requester_principal(principal)
    return {"available": model_available()}


@router.post("/respond")
def ai_respond(
    data: AIRespondRequest,
    principal: TenantPrincipal = Depends(require_principal),
):
    require_requester_principal(principal)
    try:
        response = generate_engineering_response(
            messages=[message.model_dump() for message in data.messages],
            system=data.system,
            model=data.model,
            language=data.language,
        )
    except AIGatewayUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"response": response, "model_backed": True}
