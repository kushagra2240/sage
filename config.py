"""Environment configuration for the Sage research assistant."""

import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


def get_anthropic_api_key() -> str:
    """Return the Anthropic API key from the environment."""
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise ConfigError("ANTHROPIC_API_KEY is not set")
    return key


def get_tavily_api_key() -> str:
    """Return the Tavily API key from the environment."""
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if not key:
        raise ConfigError("TAVILY_API_KEY is not set")
    return key


def validate_config() -> dict[str, str]:
    """Validate that all required API keys are present."""
    return {
        "anthropic_api_key": get_anthropic_api_key(),
        "tavily_api_key": get_tavily_api_key(),
    }
