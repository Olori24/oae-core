from .claude import ClaudeProvider
from .gemini import GeminiProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider


class ProviderManager:

    def __init__(self):
        self.providers = {
            "gemini": GeminiProvider(),
            "openai": OpenAIProvider(),
            "claude": ClaudeProvider(),
            "ollama": OllamaProvider(),
        }

        self.default = "gemini"

    def get(self, name=None):
        return self.providers.get(name or self.default)

    def list(self):
        return list(self.providers.keys())
