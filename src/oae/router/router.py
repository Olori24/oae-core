from .providers import PROVIDERS


class AIRouter:
    def __init__(self, provider="gemini"):
        if provider not in PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}")

        self.provider = PROVIDERS[provider]

    def current_provider(self):
        return self.provider

    def info(self):
        return {
            "name": self.provider.name,
            "model": self.provider.model,
            "env": self.provider.api_key_env,
      
