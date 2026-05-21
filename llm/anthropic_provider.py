"""Anthropic Claude provider with native tool_use support."""

from __future__ import annotations

from typing import Any

import anthropic

from config import get_anthropic_api_key
from llm.base import CompletionResult
from llm.planning import PLAN_TOOL, PLAN_TOOL_NAME, extract_plan_from_anthropic_message


class AnthropicProvider:
    """LLM provider using the Anthropic Messages API."""

    name = "anthropic"

    def __init__(self, api_key: str | None = None) -> None:
        self._client = anthropic.Anthropic(
            api_key=api_key or get_anthropic_api_key()
        )

    def complete(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_tokens: int,
    ) -> CompletionResult:
        message = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return _message_to_result(message)

    def create_plan_with_tools(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_tokens: int,
    ) -> list[dict[str, Any]]:
        """Generate a research plan using forced tool_use."""
        message = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            tools=[PLAN_TOOL],
            tool_choice={"type": "tool", "name": PLAN_TOOL_NAME},
        )
        return extract_plan_from_anthropic_message(message)


def _message_to_result(message: anthropic.types.Message) -> CompletionResult:
    text_blocks = [
        block.text for block in message.content if block.type == "text"
    ]
    return CompletionResult(
        text="\n".join(text_blocks),
        model=message.model,
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
        raw=message,
    )
