"""LLM provider protocol and shared types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class CompletionResult:
    """Normalized response from any LLM provider."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    raw: Any | None = None


class LLMProvider(Protocol):
    """Interface for chat completions used by Sage agents."""

    @property
    def name(self) -> str:
        """Provider identifier: 'anthropic' or 'openai'."""
        ...

    def complete(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_tokens: int,
    ) -> CompletionResult:
        """Run a system + user chat completion."""
        ...
