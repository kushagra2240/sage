"""Factory for LLM provider instances."""

from __future__ import annotations

from llm.anthropic_provider import AnthropicProvider
from llm.base import LLMProvider
from llm.openai_provider import OpenAICompatibleProvider
from config import (
    LLMProviderName,
    get_llm_provider_name,
    resolve_provider_name,
)

_provider_cache: dict[tuple[str, str | None, str | None], LLMProvider] = {}


def get_provider(
    provider: str | LLMProviderName | None = None,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
) -> LLMProvider:
    """
    Return an LLM provider instance for the given or configured backend.

    Results are cached per (provider, api_key, base_url) tuple.
    """
    name = resolve_provider_name(provider)
    cache_key = (name.value, api_key, base_url)
    if cache_key in _provider_cache:
        return _provider_cache[cache_key]

    if name == LLMProviderName.ANTHROPIC:
        instance: LLMProvider = AnthropicProvider(api_key=api_key)
    elif name == LLMProviderName.OPENAI:
        instance = OpenAICompatibleProvider(api_key=api_key, base_url=base_url)
    else:
        raise ValueError(f"Unsupported LLM provider: {name}")

    _provider_cache[cache_key] = instance
    return instance


def get_default_provider() -> LLMProvider:
    """Return a provider using environment configuration."""
    _ = get_llm_provider_name()
    return get_provider()
