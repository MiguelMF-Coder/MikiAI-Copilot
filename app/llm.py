"""Lightweight OpenAI SDK wrapper for agent calls."""

import os

MODEL = os.getenv("MODEL", "gpt-4.1-mini")


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call the configured OpenAI model and return plain text output."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "LLM is not configured. Set OPENAI_API_KEY in your .env file."

    try:
        from openai import OpenAI
    except Exception:
        return "OpenAI SDK is not installed. Install dependencies from requirements.txt."

    model = os.getenv("MODEL", MODEL)

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            max_output_tokens=300,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        text = (getattr(response, "output_text", "") or "").strip()
        if text:
            return text

        return "LLM returned an empty response."
    except Exception as exc:
        return f"LLM request failed: {exc}"
