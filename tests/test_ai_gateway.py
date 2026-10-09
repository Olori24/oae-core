from __future__ import annotations

import json

import pytest

from oae.core.ai_gateway import AIGatewayUnavailable, generate_engineering_response, model_available


def test_model_gateway_is_disabled_without_key(monkeypatch):
    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)
    assert model_available() is False
    with pytest.raises(AIGatewayUnavailable, match="not configured"):
        generate_engineering_response(messages=[{"role": "user", "content": "Build a shop."}])


def test_model_gateway_uses_configured_model(monkeypatch):
    class Response:
        def read(self):
            return json.dumps({"choices": [{"message": {"content": "I can build that."}}]}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["payload"] = json.loads(req.data.decode())
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setenv("AI_GATEWAY_API_KEY", "test-key")
    monkeypatch.setenv("OAE_AI_MODEL", "openai/test-model")
    monkeypatch.setattr("oae.core.ai_gateway.request.urlopen", fake_urlopen)

    result = generate_engineering_response(
        messages=[{"role": "user", "content": "Build a school app."}],
        system="You are OAE.",
    )

    assert result == "I can build that."
    assert captured["url"].endswith("/v1/chat/completions")
    assert captured["payload"]["model"] == "openai/test-model"
    assert captured["payload"]["messages"][0]["role"] == "system"
    assert captured["payload"]["messages"][1]["content"] == "Build a school app."


def test_coding_gateway_uses_same_ai_gateway(monkeypatch):
    from oae.core.ai_gateway import AIGatewayCodingGateway

    monkeypatch.setenv("AI_GATEWAY_API_KEY", "test-key")
    monkeypatch.setattr(
        "oae.core.ai_gateway.generate_engineering_response",
        lambda **kwargs: "proposal-json",
    )
    result = AIGatewayCodingGateway().generate(
        tenant_id="tenant-1",
        operation="code_proposal",
        model="alibaba/qwen3-coder-next",
        prompt="Return a proposal.",
    )
    assert result.content == "proposal-json"
    assert result.audit.provider == "vercel-ai-gateway"


def test_model_gateway_accepts_vercel_oidc_without_api_key(monkeypatch):
    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "oidc-token")
    from oae.core.ai_gateway import model_available
    assert model_available() is True


def test_model_gateway_adds_native_language_instruction_for_all_supported_languages(monkeypatch):
    class Response:
        def read(self):
            return json.dumps({"choices": [{"message": {"content": "translated response"}}]}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    captured = []
    def fake_urlopen(req, timeout):
        captured.append(json.loads(req.data.decode()))
        return Response()

    monkeypatch.setenv("AI_GATEWAY_API_KEY", "test-key")
    monkeypatch.setattr("oae.core.ai_gateway.request.urlopen", fake_urlopen)
    for language in ("it", "de", "fr", "es", "pt", "ar", "yo", "ha", "ig"):
        result = generate_engineering_response(
            messages=[{"role": "user", "content": "Explain this feature."}],
            language=language,
        )
        assert result == "translated response"
    assert len(captured) == 9
    for payload in captured:
        assert any(message["role"] == "system" for message in payload["messages"])
