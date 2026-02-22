"""LLM provider implementations for OpenAI and Ollama."""

from __future__ import annotations

from typing import Protocol


class LLMProvider(Protocol):
    """Common interface for text generation providers."""

    def generate(self, system_prompt: str, user_prompt: str, max_output_tokens: int) -> str:
        """Generate a response from prompts."""


class OpenAIProvider:
    """OpenAI Responses API provider."""

    def __init__(self, model: str, api_key: str | None) -> None:
        self.model = model
        self.api_key = api_key

    def generate(self, system_prompt: str, user_prompt: str, max_output_tokens: int) -> str:
        if not self.api_key:
            return "LLM is not configured. Set OPENAI_API_KEY in your .env file."

        try:
            from openai import OpenAI
        except Exception:
            return "OpenAI SDK is not installed. Install dependencies from requirements.txt."

        try:
            client = OpenAI(api_key=self.api_key)
            response = client.responses.create(
                model=self.model,
                max_output_tokens=max_output_tokens,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            text = (getattr(response, "output_text", "") or "").strip()
            return text or "LLM returned an empty response."
        except Exception as exc:
            return f"LLM request failed: {exc}"


class OllamaProvider:
    """Local Ollama HTTP provider."""

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str, max_output_tokens: int) -> str:
        if not self.model:
            return "Ollama is not configured. Set OLLAMA_MODEL in your environment."

        combined_prompt = (
            "System instructions:\n"
            f"{system_prompt}\n\n"
            "User request:\n"
            f"{user_prompt}"
        )

        payload = {
            "model": self.model,
            "prompt": combined_prompt,
            "stream": False,
            "options": {"num_predict": max_output_tokens},
        }

        try:
            import httpx

            response = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30.0,
            )
        except Exception:
            return (
                "Ollama request failed. Ensure Ollama is running at "
                f"{self.base_url} (try: ollama serve)."
            )

        if response.status_code != 200:
            return f"Ollama request failed with HTTP {response.status_code}."

        try:
            data = response.json()
        except Exception:
            return "Ollama returned invalid JSON response."

        text = str(data.get("response", "")).strip()
        return text or "Ollama returned an empty response."
