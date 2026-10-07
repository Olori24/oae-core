"""Optional model gateway for OAE's conversational engineering brain.

The gateway is deliberately isolated from repository execution. It can reason over
user intent and supplied context, but it cannot mutate workspaces or invoke tools.
Set AI_GATEWAY_API_KEY to enable model-backed responses.
"""
from __future__ import annotations

import json
import os
from urllib import request
from urllib.error import HTTPError, URLError


class AIGatewayUnavailable(RuntimeError):
    """Raised when the configured model gateway cannot be reached or is not configured."""


def model_available() -> bool:
    return bool(os.getenv("AI_GATEWAY_API_KEY"))


def generate_engineering_response(
    *,
    messages: list[dict[str, str]],
    model: str | None = None,
    system: str | None = None,
) -> str:
    api_key = os.getenv("AI_GATEWAY_API_KEY")
    if not api_key:
        raise AIGatewayUnavailable("AI model gateway is not configured.")

    selected_model = model or os.getenv("OAE_AI_MODEL", "openai/gpt-5.6-sol")
    prompt_messages: list[dict[str, str]] = []
    if system:
        prompt_messages.append({"role": "system", "content": system})
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
