"""Run a redacted, non-sensitive smoke test against a private OAE model host."""

from __future__ import annotations

import ipaddress
import json
import socket
from dataclasses import asdict
from urllib.parse import urlparse

from oae.api.config import settings
from oae.providers.open_weight import (
    OpenWeightModelGateway,
    OpenWeightProviderError,
    open_weight_config_from_settings,
)

APPROVED_SMOKE_MODEL = "qwen3:8b"
SMOKE_TENANT_ID = "oae-open-weight-smoke-test"
SMOKE_PROMPT = (
    "Summarize the OAE governance sequence UNDERSTAND, PLAN, AUTHORIZE, EXECUTE, "
    "VERIFY, RECORD in three concise bullets. Do not state that you performed any action."
)


def private_endpoint(endpoint: str) -> bool:
    """Accept compose-local, loopback, or fully private IP endpoints only."""
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    if parsed.hostname == "ollama":
        return True
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port)}
    except socket.gaierror:
        return False
    if not addresses:
        return False
    for address in addresses:
        try:
            parsed_address = ipaddress.ip_address(address)
        except ValueError:
            return False
        if not (parsed_address.is_private or parsed_address.is_loopback or parsed_address.is_link_local):
            return False
    return True


def smoke_gateway_from_settings() -> OpenWeightModelGateway:
    """Build the configured gateway only when its approved private profile is active."""
    config = open_weight_config_from_settings(settings)
    if not config.enabled:
        raise OpenWeightProviderError("Open-weight inference is disabled by configuration.")
    if APPROVED_SMOKE_MODEL not in config.allowed_models:
        raise OpenWeightProviderError("Qwen3 8B is not in the approved OAE model allowlist.")
    if not private_endpoint(config.endpoint):
        raise OpenWeightProviderError("Open-weight smoke test requires a private model endpoint.")
    return OpenWeightModelGateway(config)


def run_smoke_test(gateway: OpenWeightModelGateway):
    """Run a fixed non-sensitive review request and return audit metadata only."""
    return gateway.generate(
        tenant_id=SMOKE_TENANT_ID,
        operation="review",
        model=APPROVED_SMOKE_MODEL,
        prompt=SMOKE_PROMPT,
    ).audit


def main() -> int:
    try:
        audit = run_smoke_test(smoke_gateway_from_settings())
    except OpenWeightProviderError as exc:
        print(json.dumps({"status": "failed", "reason": str(exc)}))
        return 2
    print(json.dumps({"status": "passed", "audit": asdict(audit)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
