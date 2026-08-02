from .base import Provider


class OllamaProvider(Provider):
    name = "ollama"

    def generate(self, prompt):
        return f"Ollama received: {prompt}"

    def health(self):
        return True
