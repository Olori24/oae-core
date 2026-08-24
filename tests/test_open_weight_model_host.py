import json

import pytest

from oae.providers.open_weight import (
    OpenWeightModelConfig,
    OpenWeightModelGateway,
    OpenWeightProviderError,
)
from oae.providers.open_weight_smoke_test import private_endpoint, run_smoke_test


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps({"model": "qwen3:8b", "message": {"content": "Three bounded bullets."}}).encode(
            "utf-8"
        )


def test_private_endpoint_accepts_compose_local_model_service():
    assert private_endpoint("http://ollama:11434")


def test_private_endpoint_rejects_public_model_service(monkeypatch):
    monkeypatch.setattr(
        "oae.providers.open_weight_smoke_test.socket.getaddrinfo",
        lambda *_args, **_kwargs: [(None, None, None, None, ("8.8.8.8", 11434))],
    )

    assert not private_endpoint("https://model.example.test")


def test_smoke_test_returns_redacted_audit_metadata_only():
    gateway = OpenWeightModelGateway(
        OpenWeightModelConfig(
            enabled=True,
            endpoint="http://ollama:11434",
            allowed_models=("qwen3:8b",),
        ),
        opener=lambda *_args, **_kwargs: FakeResponse(),
    )

    audit = run_smoke_test(gateway)

    assert audit.model == "qwen3:8b"
    assert audit.operation == "review"
    assert audit.status == "completed"
    assert not hasattr(audit, "content")


def test_smoke_test_rejects_a_gateway_without_an_approved_model():
    gateway = OpenWeightModelGateway(
        OpenWeightModelConfig(
            enabled=True,
            endpoint="http://ollama:11434",
            allowed_models=("different-model",),
        )
    )

    with pytest.raises(OpenWeightProviderError, match="allowlist"):
        run_smoke_test(gateway)
