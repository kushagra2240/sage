"""Environment configuration for the Sage research assistant."""

import os
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


class LLMProviderName(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"
DEFAULT_OPENAI_MODEL = "meta-llama/llama-3.3-70b-instruct"
DEFAULT_OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
OPENAI_MAX_TOKENS_PARAMETERS = {
    "auto",
    "max_tokens",
    "max_completion_tokens",
}


def get_llm_provider_name() -> LLMProviderName:
    """Return the configured LLM provider (default: anthropic)."""
    raw = os.getenv("LLM_PROVIDER", "anthropic").strip().lower()
    try:
        return LLMProviderName(raw)
    except ValueError as exc:
        raise ConfigError(
            f"LLM_PROVIDER must be 'anthropic' or 'openai', got: {raw!r}"
        ) from exc


def resolve_provider_name(
    provider: str | LLMProviderName | None,
) -> LLMProviderName:
    """Resolve an optional override to a provider enum."""
    if provider is None:
        return get_llm_provider_name()
    if isinstance(provider, LLMProviderName):
        return provider
    try:
        return LLMProviderName(provider.strip().lower())
    except ValueError as exc:
        raise ConfigError(
            f"LLM_PROVIDER must be 'anthropic' or 'openai', got: {provider!r}"
        ) from exc


def get_default_model(provider: LLMProviderName | None = None) -> str:
    """Return the default model id for the active or given provider."""
    name = provider or get_llm_provider_name()
    if name == LLMProviderName.ANTHROPIC:
        return os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL).strip()
    return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip()


def get_anthropic_api_key() -> str:
    """Return the Anthropic API key from the environment."""
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise ConfigError("ANTHROPIC_API_KEY is not set")
    return key


def get_openai_api_key() -> str:
    """Return the OpenAI-compatible API key from the environment."""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise ConfigError("OPENAI_API_KEY is not set")
    return key


def get_openai_base_url() -> str:
    """Return the OpenAI-compatible API base URL."""
    url = os.getenv("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL).strip()
    if not url:
        raise ConfigError("OPENAI_BASE_URL is not set")
    return url


def get_openai_max_tokens_parameter() -> str:
    """Return the output-token parameter for an OpenAI-compatible endpoint.

    ``auto`` selects ``max_completion_tokens`` for GPT-5 and reasoning model
    families, and the legacy ``max_tokens`` parameter for other compatible
    endpoints such as Ollama. Set the environment variable explicitly when an
    OpenAI-compatible gateway has different requirements.
    """
    value = os.getenv("OPENAI_MAX_TOKENS_PARAMETER", "auto").strip().lower()
    if value not in OPENAI_MAX_TOKENS_PARAMETERS:
        choices = ", ".join(sorted(OPENAI_MAX_TOKENS_PARAMETERS))
        raise ConfigError(
            f"OPENAI_MAX_TOKENS_PARAMETER must be one of: {choices}; got: {value!r}"
        )
    return value


def get_tavily_api_key() -> str:
    """Return the Tavily API key from the environment."""
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if not key:
        raise ConfigError("TAVILY_API_KEY is not set")
    return key


def validate_config(provider: str | LLMProviderName | None = None) -> dict[str, str]:
    """Validate API keys for the active LLM provider and Tavily."""
    name = resolve_provider_name(provider)
    result: dict[str, str] = {
        "llm_provider": name.value,
        "tavily_api_key": get_tavily_api_key(),
        "model": get_default_model(name),
    }

    if name == LLMProviderName.ANTHROPIC:
        result["anthropic_api_key"] = get_anthropic_api_key()
    else:
        result["openai_api_key"] = get_openai_api_key()
        result["openai_base_url"] = get_openai_base_url()
        result["openai_max_tokens_parameter"] = get_openai_max_tokens_parameter()

    return result
