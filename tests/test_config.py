"""Tests for config module."""

import os
from unittest.mock import patch

import pytest

from config import (
    ConfigError,
    LLMProviderName,
    get_anthropic_api_key,
    get_default_model,
    get_llm_provider_name,
    get_openai_api_key,
    get_tavily_api_key,
    validate_config,
)


class TestGetLlmProviderName:
    def test_defaults_to_anthropic(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("LLM_PROVIDER", None)
            assert get_llm_provider_name() == LLMProviderName.ANTHROPIC

    def test_accepts_openai(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai"}, clear=True):
            assert get_llm_provider_name() == LLMProviderName.OPENAI

    def test_raises_on_invalid_provider(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "invalid"}, clear=True):
            with pytest.raises(ConfigError, match="LLM_PROVIDER"):
                get_llm_provider_name()


class TestGetAnthropicApiKey:
    def test_returns_key_when_set(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-anthropic"}):
            assert get_anthropic_api_key() == "sk-test-anthropic"

    def test_raises_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
                get_anthropic_api_key()


class TestGetOpenaiApiKey:
    def test_returns_key_when_set(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-openai"}):
            assert get_openai_api_key() == "sk-test-openai"

    def test_raises_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENAI_API_KEY", None)
            with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
                get_openai_api_key()


class TestGetTavilyApiKey:
    def test_returns_key_when_set(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test"}):
            assert get_tavily_api_key() == "tvly-test"

    def test_raises_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("TAVILY_API_KEY", None)
            with pytest.raises(ConfigError, match="TAVILY_API_KEY"):
                get_tavily_api_key()


class TestGetDefaultModel:
    def test_anthropic_default(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_MODEL", None)
            assert "claude" in get_default_model(LLMProviderName.ANTHROPIC)

    def test_openai_default(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENAI_MODEL", None)
            model = get_default_model(LLMProviderName.OPENAI)
            assert "llama" in model.lower() or "meta" in model.lower()


class TestValidateConfig:
    def test_anthropic_provider_keys(self):
        env = {
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "sk-anthropic",
            "TAVILY_API_KEY": "tvly-key",
        }
        with patch.dict(os.environ, env, clear=True):
            result = validate_config()
            assert result["llm_provider"] == "anthropic"
            assert result["anthropic_api_key"] == "sk-anthropic"
            assert "openai_api_key" not in result

    def test_openai_provider_keys(self):
        env = {
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "sk-openai",
            "OPENAI_BASE_URL": "http://localhost:11434/v1",
            "TAVILY_API_KEY": "tvly-key",
        }
        with patch.dict(os.environ, env, clear=True):
            result = validate_config(provider="openai")
            assert result["llm_provider"] == "openai"
            assert result["openai_api_key"] == "sk-openai"
            assert "anthropic_api_key" not in result

    def test_raises_when_tavily_missing(self):
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-a"},
            clear=True,
        ):
            with pytest.raises(ConfigError, match="TAVILY"):
                validate_config()
