import json

import pytest

from oae.providers.open_weight import (
    OpenWeightModelConfig,
    OpenWeightModelGateway,
    OpenWeightProviderError,
    open_weight_config_from_settings,
)


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def configured_gateway(opener):
    return OpenWeightModelGateway(
        OpenWeightModelConfig(
            enabled=True,
            endpoint="http://ollama:11434",
            allowed_models=("qwen3:8b",),
            max_prompt_chars=100,
            max_output_tokens=64,
            max_response_chars=256,
        ),
        opener=opener,
    )


def test_gateway_sends_bounded_non_streaming_request_and_returns_redacted_audit_metadata():
    captured = {}

    def opener(http_request, timeout):
        captured["url"] = http_request.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(http_request.data.decode("utf-8"))
        return FakeResponse({"model": "qwen3:8b", "message": {"content": "Review findings."}})

    result = configured_gateway(opener).generate(
        tenant_id="tenant-sensitive-name",
        operation="review",
        model="qwen3:8b",
        prompt="Review this bounded change.",
    )

    assert captured["url"] == "http://ollama:11434/api/chat"
    assert captured["timeout"] == 30
    assert captured["body"]["stream"] is False
    assert captured["body"]["options"] == {"temperature": 0.2, "num_predict": 64}
    assert "tools" not in captured["body"]
    assert result.content == "Review findings."
    assert result.audit.operation == "review"
    assert result.audit.tenant_pseudonym != "tenant-sensitive-name"
    assert result.audit.input_chars == len("Review this bounded change.")


@pytest.mark.parametrize("operation", ["build", "execute", ""])
def test_gateway_rejects_unapproved_operations(operation):
    gateway = configured_gateway(lambda *_args, **_kwargs: pytest.fail("network call is forbidden"))

    with pytest.raises(OpenWeightProviderError, match="not permitted"):
        gateway.generate(
            tenant_id="tenant-a",
            operation=operation,
            model="qwen3:8b",
            prompt="Review this.",
        )


def test_gateway_rejects_disabled_provider_without_network_access():
    gateway = OpenWeightModelGateway(
        OpenWeightModelConfig(
            enabled=False,
            endpoint="http://ollama:11434",
            allowed_models=("qwen3:8b",),
        ),
        opener=lambda *_args, **_kwargs: pytest.fail("network call is forbidden"),
    )

    with pytest.raises(OpenWeightProviderError, match="disabled"):
        gateway.generate(
            tenant_id="tenant-a",
            operation="analyze",
            model="qwen3:8b",
            prompt="Analyze this.",
        )


def test_gateway_rejects_models_outside_the_allowlist_without_network_access():
    gateway = configured_gateway(lambda *_args, **_kwargs: pytest.fail("network call is forbidden"))

    with pytest.raises(OpenWeightProviderError, match="allowlist"):
        gateway.generate(
            tenant_id="tenant-a",
            operation="analyze",
            model="unapproved-model",
            prompt="Analyze this.",
        )


def test_gateway_rejects_unexpected_model_identity():
    gateway = configured_gateway(
        lambda *_args, **_kwargs: FakeResponse(
            {"model": "different-model", "message": {"content": "Response."}}
        )
    )

    with pytest.raises(OpenWeightProviderError, match="unexpected model"):
        gateway.generate(
            tenant_id="tenant-a",
            operation="verify",
            model="qwen3:8b",
            prompt="Verify this.",
        )


def test_provider_configuration_is_derived_from_server_side_settings_only():
    class Settings:
        open_weight_model_enabled = True
        open_weight_model_endpoint = "http://ollama:11434"
        open_weight_model_allowed_models = ["qwen3:8b"]
        open_weight_model_timeout_seconds = 20
        open_weight_model_max_prompt_chars = 4_000
        open_weight_model_max_output_tokens = 500
        open_weight_model_max_response_chars = 8_000

    config = open_weight_config_from_settings(Settings())

    assert config.enabled is True
    assert config.endpoint == "http://ollama:11434"
    assert config.allowed_models == ("qwen3:8b",)
    assert config.max_output_tokens == 500
