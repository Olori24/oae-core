from dataclasses import dataclass


@dataclass
class Provider:
    name: str
    model: str
    api_key_env: str


PROVIDERS = {
    "gemini": Provider(
        "gemini",
        "gemini-2.5-pro",
        "GEMINI_API_KEY",
    ),

    "openai": Provider(
        "openai",
        "gpt-5.5",
        "OPENAI_API_KEY",
    ),

    "anthropic": Provider(
        "anthropic",
        "claude",
        "ANTHROPIC_API_KEY",
    ),

    "grok": Provider(
        "grok",
        "grok",
        "XAI_API_KEY",
    ),

    "ollama": Provider(
        "ollama",
        "llama3",
        "OLLAMA_HOST",
    ),
}
