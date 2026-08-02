from .base import Provider


class GeminiProvider(Provider):
    name = "gemini"

    def generate(self, prompt):
        return f"Gemini received: {prompt}"

    def health(self):
        return True
