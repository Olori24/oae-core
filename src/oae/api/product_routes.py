"""Product-builder API for non-coder OAE users."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from oae.api.auth import TenantPrincipal, require_principal, require_requester_principal
from oae.core.product_builder import build_product_brief

router = APIRouter(prefix="/v1/product", tags=["product-builder"])

class ProductBriefRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    idea: str = Field(min_length=10, max_length=12000)
    context: list[dict[str, str]] = Field(default_factory=list, max_length=12)

@router.post("/brief")
def create_product_brief(
    data: ProductBriefRequest,
    principal: TenantPrincipal = Depends(require_principal),
) -> dict[str, Any]:
    require_requester_principal(principal)
    brief = build_product_brief(data.idea, data.context)
    return {"brief": brief, "ready": bool(brief.get("build_ready")), "next": (
        "The product brief is complete enough to propose an engineering plan."
        if brief.get("build_ready")
        else "Answer the missing product questions before OAE proposes implementation."
    )}
