"""Bounded gateway for an approved open-weight model endpoint.

The gateway uses Ollama's non-streaming chat endpoint. It intentionally accepts no
tools, no arbitrary endpoint, no build operation, and no request without a tenant.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib import error, request
from urllib.parse import urlparse

MODEL_NAME_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
ALLOWED_OPERATIONS = frozenset({"analyze", "review", "verify"})


class OpenWeightProviderError(RuntimeError):
    """Raised when the bounded open-weight gateway cannot safely complete a request."""


@dataclass(frozen=True)
class OpenWeightModelConfig:
    enabled: bool = False
    endpoint: str = ""
    allowed_models: tuple[str, ...] = ()
    timeout_seconds: int = 30
    max_prompt_chars: int = 12_000
    max_output_tokens: int = 1_024
    max_response_chars: int = 16_000


@dataclass(frozen=True)
class OpenWeightInvocationAudit:
    """Redacted metadata suitable for an audit event; it never holds prompt or reply text."""

    provider: str
    tenant_pseudonym: str
    model: str
    operation: str
    status: str
    input_chars: int
    output_chars: int
    duration_ms: int


@dataclass(frozen=True)
class OpenWeightModelResponse:
    content: str
    audit: OpenWeightInvocationAudit


def open_weight_config_from_settings(settings: Any) -> OpenWeightModelConfig:
    """Build provider configuration from server-side settings without exposing credentials."""
    return OpenWeightModelConfig(
        enabled=settings.open_weight_model_enabled,
        endpoint=settings.open_weight_model_endpoint,
        allowed_models=tuple(settings.open_weight_model_allowed_models),
        timeout_seconds=settings.open_weight_model_timeout_seconds,
        max_prompt_chars=settings.open_weight_model_max_prompt_chars,
        max_output_tokens=settings.open_weight_model_max_output_tokens,
        max_response_chars=settings.open_weight_model_max_response_chars,
    )


class OpenWeightModelGateway:
    """Call a configured Ollama endpoint with a strict OAE request boundary."""

    def __init__(
        self,
        config: OpenWeightModelConfig,
        opener: Callable[..., Any] = request.urlopen,
    ) -> None:
        self._config = config
        self._opener = opener

    def generate(
        self,
        *,
        tenant_id: str,
        operation: str,
        model: str,
        prompt: str,
    ) -> OpenWeightModelResponse:
        """Generate bounded planning text for an approved tenant and safe operation."""
        self._validate_request(tenant_id=tenant_id, operation=operation, model=model, prompt=prompt)
        started = time.monotonic()
        payload = {
            "model": model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an OAE planning assistant. Return analysis only. Do not claim that "
                        "you executed commands, changed files, approved work, or verified evidence."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": 0.2, "num_predict": self._config.max_output_tokens},
        }
        request_data = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            f"{self._normalized_endpoint()}/api/chat",
            data=request_data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with self._opener(http_request, timeout=self._config.timeout_seconds) as response:
                body = response.read()
        except error.HTTPError as exc:
            raise OpenWeightProviderError(
                f"Open-weight inference endpoint returned HTTP status {exc.code}."
            ) from exc
        except (error.URLError, OSError, TimeoutError) as exc:
            raise OpenWeightProviderError("Open-weight inference endpoint is unavailable.") from exc

        duration_ms = int((time.monotonic() - started) * 1_000)
        content, returned_model = self._parse_response(body)
        if returned_model != model:
            raise OpenWeightProviderError("Open-weight endpoint returned an unexpected model identity.")
        if len(content) > self._config.max_response_chars:
            raise OpenWeightProviderError("Open-weight response exceeded the configured character boundary.")
        return OpenWeightModelResponse(
            content=content,
            audit=OpenWeightInvocationAudit(
                provider="ollama",
                tenant_pseudonym=self._tenant_pseudonym(tenant_id),
                model=model,
                operation=operation,
                status="completed",
                input_chars=len(prompt),
                output_chars=len(content),
                duration_ms=duration_ms,
            ),
        )

    def health(self) -> bool:
        """Check endpoint reachability without returning model inventory or endpoint diagnostics."""
        if not self._config.enabled or not self._config.endpoint:
            return False
        try:
            with self._opener(
                request.Request(f"{self._normalized_endpoint()}/api/tags", method="GET"),
                timeout=self._config.timeout_seconds,
            ):
                return True
        except (OpenWeightProviderError, error.URLError, OSError, TimeoutError):
            return False

    def _validate_request(self, *, tenant_id: str, operation: str, model: str, prompt: str) -> None:
        if not self._config.enabled:
            raise OpenWeightProviderError("Open-weight inference is disabled by configuration.")
        if not tenant_id.strip():
            raise OpenWeightProviderError("A tenant identifier is required for open-weight inference.")
        if operation not in ALLOWED_OPERATIONS:
            raise OpenWeightProviderError("This OAE operation is not permitted for open-weight inference.")
        if not MODEL_NAME_PATTERN.fullmatch(model) or model not in self._config.allowed_models:
            raise OpenWeightProviderError("The requested model is not in the approved model allowlist.")
        if not prompt.strip() or len(prompt) > self._config.max_prompt_chars:
            raise OpenWeightProviderError("Prompt content is absent or exceeds the configured character boundary.")
        if not self._config.endpoint.strip():
            raise OpenWeightProviderError("Open-weight endpoint is not configured.")
        self._normalized_endpoint()

    def _normalized_endpoint(self) -> str:
        parsed = urlparse(self._config.endpoint)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise OpenWeightProviderError("Open-weight endpoint must be an absolute HTTP or HTTPS URL.")
        if parsed.params or parsed.query or parsed.fragment:
            raise OpenWeightProviderError("Open-weight endpoint must not include parameters, a query, or a fragment.")
        return self._config.endpoint.rstrip("/")

    def _parse_response(self, body: bytes) -> tuple[str, str]:
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OpenWeightProviderError("Open-weight endpoint returned an invalid JSON response.") from exc
        if not isinstance(payload, Mapping):
            raise OpenWeightProviderError("Open-weight endpoint returned an invalid response object.")
        message = payload.get("message")
        model = payload.get("model")
        if not isinstance(message, Mapping) or not isinstance(message.get("content"), str):
            raise OpenWeightProviderError("Open-weight endpoint response did not contain assistant content.")
        if not isinstance(model, str):
            raise OpenWeightProviderError("Open-weight endpoint response did not identify a model.")
        return message["content"], model

    @staticmethod
    def _tenant_pseudonym(tenant_id: str) -> str:
        return hashlib.sha256(tenant_id.encode("utf-8")).hexdigest()[:16]
