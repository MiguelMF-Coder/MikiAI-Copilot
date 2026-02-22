"""Provider-agnostic LLM wrapper used by agents."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.llm.providers import LLMProvider


def _load_providers_module():
    """Load provider implementations from app/llm/providers.py."""
    providers_path = Path(__file__).with_name("llm") / "providers.py"
    spec = importlib.util.spec_from_file_location("app_llm_providers", providers_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_providers = _load_providers_module()

MAX_OUTPUT_TOKENS = 300
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.1:8b"


class _ErrorProvider:
    """Fallback provider for invalid configuration."""

    def __init__(self, message: str) -> None:
        self.message = message

    def generate(self, system_prompt: str, user_prompt: str, max_output_tokens: int) -> str:
        return self.message


def _get_provider() -> "LLMProvider":
    """Instantiate the provider configured in environment variables."""
    if _providers is None:
        return _ErrorProvider("LLM providers module is unavailable.")

    provider_name = os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER).strip().lower()

    if provider_name == "openai":
        return _providers.OpenAIProvider(
            model=os.getenv("MODEL", DEFAULT_MODEL),
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    if provider_name == "ollama":
        return _providers.OllamaProvider(
            base_url=os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
            model=os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
        )

    return _ErrorProvider(
        f"Unsupported LLM_PROVIDER '{provider_name}'. Use 'openai' or 'ollama'."
    )


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Generate text using the configured LLM provider."""
    try:
        provider = _get_provider()
        return provider.generate(system_prompt, user_prompt, MAX_OUTPUT_TOKENS)
    except Exception as exc:
        return f"LLM request failed: {exc}"
