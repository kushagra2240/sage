"""OpenAI-compatible provider (OpenRouter, Together, Groq, Ollama)."""

from __future__ import annotations

from typing import Any

from openai import OpenAI

from config import get_openai_api_key, get_openai_base_url
from llm.base import CompletionResult
from llm.planning import parse_plan_from_json


class OpenAICompatibleProvider:
    """LLM provider using any OpenAI-compatible chat completions API."""

    name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self._client = OpenAI(
            api_key=api_key or get_openai_api_key(),
            base_url=base_url or get_openai_base_url(),
        )

    def complete(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_tokens: int,
    ) -> CompletionResult:
        response = self._client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return _response_to_result(response)

    def create_plan_json(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_tokens: int,
    ) -> list[dict[str, Any]]:
        """Generate a research plan via JSON-only completion."""
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            response = self._client.chat.completions.create(
                **kwargs,
                response_format={"type": "json_object"},
            )
        except Exception:
            response = self._client.chat.completions.create(**kwargs)

        result = _response_to_result(response)
        return parse_plan_from_json(result.text)


def _response_to_result(response: Any) -> CompletionResult:
    choice = response.choices[0]
    usage = response.usage
    return CompletionResult(
        text=choice.message.content or "",
        model=response.model,
        input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
        output_tokens=getattr(usage, "completion_tokens", 0) or 0,
        raw=response,
    )
