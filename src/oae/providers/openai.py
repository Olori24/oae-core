from .base import Provider


class OpenAIProvider(Provider):
    name = "openai"

    def generate(self, prompt):
        return f"OpenAI received: {prompt}"

    def health(self):
        return True
