"""Optional model gateway for OAE's conversational engineering brain.

The gateway is deliberately isolated from repository execution. It can reason over
user intent and supplied context, but it cannot mutate workspaces or invoke tools.
Set AI_GATEWAY_API_KEY to enable model-backed responses.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from urllib import request
from urllib.error import HTTPError, URLError


class AIGatewayUnavailable(RuntimeError):
    """Raised when the configured model gateway cannot be reached or is not configured."""

@dataclass(frozen=True)
class AIGatewayAudit:
    provider: str
    tenant_pseudonym: str
    model: str
    operation: str
    status: str
    input_chars: int
    output_chars: int
    duration_ms: int

@dataclass(frozen=True)
class AIGatewayResponse:
    content: str
    audit: AIGatewayAudit

class AIGatewayCodingGateway:
    """Adapter for the coding brain using the same governed gateway as chat."""

    def generate(self, *, tenant_id: str, operation: str, model: str, prompt: str) -> AIGatewayResponse:
        if operation not in {"code_proposal", "code_repair"}:
            raise AIGatewayUnavailable("This operation is not permitted for the coding gateway.")
        started = time.monotonic()
        content = generate_engineering_response(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            system=(
                "You are OAE's bounded coding brain. Propose code only. "
                "Never claim execution, verification, deployment, or repository mutation."
            ),
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        return AIGatewayResponse(
            content=content,
            audit=AIGatewayAudit(
                provider="vercel-ai-gateway",
                tenant_pseudonym=hashlib.sha256(tenant_id.encode()).hexdigest()[:16],
                model=model,
                operation=operation,
                status="completed",
                input_chars=len(prompt),
                output_chars=len(content),
                duration_ms=duration_ms,
            ),
        )


def model_available() -> bool:
    return bool(os.getenv("AI_GATEWAY_API_KEY") or os.getenv("VERCEL_OIDC_TOKEN"))


def generate_engineering_response(
    *,
    messages: list[dict[str, str]],
    model: str | None = None,
    system: str | None = None,
    language: str = "en",
) -> str:
    api_key = os.getenv("AI_GATEWAY_API_KEY") or os.getenv("VERCEL_OIDC_TOKEN")
    if not api_key:
        raise AIGatewayUnavailable("AI model gateway is not configured.")

    selected_model = model or os.getenv("OAE_AI_MODEL", "alibaba/qwen3-coder-next")
    prompt_messages: list[dict[str, str]] = []
    if system:
        prompt_messages.append({"role": "system", "content": system})
    language_names = {"en": "English", "it": "Italian", "de": "German", "fr": "French", "es": "Spanish", "pt": "Portuguese", "ar": "Arabic", "yo": "Yoruba", "ha": "Hausa", "ig": "Igbo"}
    if language != "en":
        prompt_messages.append({"role": "system", "content": f"Respond entirely in {language_names.get(language, 'English')}. Preserve code and technical identifiers."})
    prompt_messages.extend(messages[-24:])

    payload = json.dumps(
        {"model": selected_model, "messages": prompt_messages},
        separators=(",", ":"),
    ).encode("utf-8")
    req = request.Request(
        "https://ai-gateway.vercel.sh/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=45) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise AIGatewayUnavailable("The configured AI model gateway is unavailable.") from exc

    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AIGatewayUnavailable("The AI model returned no response.")
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise AIGatewayUnavailable("The AI model returned an empty response.")
    return content.strip()
