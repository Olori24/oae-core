from .base import Provider


class ClaudeProvider(Provider):
    name = "claude"

    def generate(self, prompt):
        return f"Claude received: {prompt}"

    def health(self):
        return True
