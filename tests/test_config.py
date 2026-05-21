"""Tests for config module."""

import os
from unittest.mock import patch

import pytest

from config import ConfigError, get_anthropic_api_key, get_tavily_api_key, validate_config


class TestGetAnthropicApiKey:
    def test_returns_key_when_set(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-anthropic"}):
            assert get_anthropic_api_key() == "sk-test-anthropic"

    def test_raises_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
                get_anthropic_api_key()

    def test_raises_when_empty(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "   "}):
            with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
                get_anthropic_api_key()


class TestGetTavilyApiKey:
    def test_returns_key_when_set(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test"}):
            assert get_tavily_api_key() == "tvly-test"

    def test_raises_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("TAVILY_API_KEY", None)
            with pytest.raises(ConfigError, match="TAVILY_API_KEY"):
                get_tavily_api_key()


class TestValidateConfig:
    def test_returns_both_keys(self):
        env = {
            "ANTHROPIC_API_KEY": "sk-anthropic",
            "TAVILY_API_KEY": "tvly-key",
        }
        with patch.dict(os.environ, env, clear=True):
            result = validate_config()
            assert result == {
                "anthropic_api_key": "sk-anthropic",
                "tavily_api_key": "tvly-key",
            }

    def test_raises_when_anthropic_missing(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-key"}, clear=True):
            with pytest.raises(ConfigError):
                validate_config()
