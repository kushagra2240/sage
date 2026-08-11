"""OpenAI-compatible provider (OpenRouter, Together, Groq, Ollama)."""

from __future__ import annotations

from typing import Any

from openai import OpenAI

from config import (
    get_openai_api_key,
    get_openai_base_url,
    get_openai_max_tokens_parameter,
)
from llm.base import CompletionResult
from llm.planning import parse_plan_from_json


class OpenAICompatibleProvider:
    """LLM provider using any OpenAI-compatible chat completions API."""

    name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        max_tokens_parameter: str | None = None,
    ) -> None:
        self._client = OpenAI(
            api_key=api_key or get_openai_api_key(),
            base_url=base_url or get_openai_base_url(),
        )
        self._max_tokens_parameter = (
            max_tokens_parameter or get_openai_max_tokens_parameter()
        )

    def _output_token_kwargs(self, model: str, max_tokens: int) -> dict[str, int]:
        """Translate Sage's provider-neutral output limit to the API dialect.

        Anthropic always calls its limit ``max_tokens``. OpenAI's newest GPT
        and reasoning models instead require ``max_completion_tokens``;
        popular OpenAI-compatible servers such as Ollama still use
        ``max_tokens``. An environment override handles gateways that differ
        from the model-name heuristic.
        """
        parameter = self._max_tokens_parameter
        if parameter == "auto":
            model_name = model.strip().lower()
            parameter = (
                "max_completion_tokens"
                if model_name.startswith(("gpt-5", "o1", "o3", "o4"))
                else "max_tokens"
            )
        return {parameter: max_tokens}

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
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            **self._output_token_kwargs(model, max_tokens),
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
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            **self._output_token_kwargs(model, max_tokens),
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
    text = choice.message.content or ""
    if not text.strip():
        finish_reason = getattr(choice, "finish_reason", None)
        detail = f" (finish reason: {finish_reason})" if finish_reason else ""
        raise RuntimeError(
            f"{response.model} returned no text{detail}. The model may have used "
            "its completion budget for reasoning; increase the stage output-token "
            "limit or use a lower reasoning effort."
        )
    return CompletionResult(
        text=text,
        model=response.model,
        input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
        output_tokens=getattr(usage, "completion_tokens", 0) or 0,
        raw=response,
    )
