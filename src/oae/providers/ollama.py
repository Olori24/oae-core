from oae.api.config import settings

from .base import Provider
from .open_weight import OpenWeightModelGateway, open_weight_config_from_settings


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(self, gateway: OpenWeightModelGateway | None = None):
        self.gateway = gateway or OpenWeightModelGateway(open_weight_config_from_settings(settings))

    def generate(self, prompt: str):
        raise RuntimeError(
            "Use generate_for_tenant with an approved model and bounded OAE operation; "
            "unscoped open-weight generation is not permitted."
        )

    def generate_for_tenant(self, *, tenant_id: str, operation: str, model: str, prompt: str):
        return self.gateway.generate(
            tenant_id=tenant_id,
            operation=operation,
            model=model,
            prompt=prompt,
        )

    def health(self):
        return self.gateway.health()
