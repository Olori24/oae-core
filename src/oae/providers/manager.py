from .gemini import GeminiProvider
from .openai import OpenAIProvider
from .claude import ClaudeProvider
from .ollama import OllamaProvider


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
