"""Tests for llm package."""

import json
from unittest.mock import MagicMock, patch

import pytest

from config import ConfigError, LLMProviderName
from llm.anthropic_provider import AnthropicProvider
from llm.base import CompletionResult
from llm.factory import get_provider
from llm.openai_provider import OpenAICompatibleProvider
from llm.planning import (
    extract_plan_from_anthropic_message,
    parse_plan_from_json,
)

VALID_STEPS = [
    {"step": 1, "search_query": "topic overview", "goal": "Overview"},
    {"step": 2, "search_query": "recent developments", "goal": "Trends"},
    {"step": 3, "search_query": "key challenges", "goal": "Challenges"},
]


class TestParsePlanFromJson:
    def test_parses_object_with_steps(self):
        payload = json.dumps({"steps": VALID_STEPS})
        plan = parse_plan_from_json(payload)
        assert len(plan) == 3
        assert plan[0]["search_query"] == "topic overview"

    def test_strips_markdown_fences(self):
        payload = "```json\n" + json.dumps({"steps": VALID_STEPS}) + "\n```"
        plan = parse_plan_from_json(payload)
        assert len(plan) == 3

    def test_raises_on_invalid_json(self):
        with pytest.raises(RuntimeError, match="Invalid JSON"):
            parse_plan_from_json("not json at all")

    def test_raises_on_too_few_steps(self):
        payload = json.dumps({"steps": VALID_STEPS[:1]})
        with pytest.raises(ValueError, match="between 3 and 5"):
            parse_plan_from_json(payload)


class TestExtractPlanFromAnthropicMessage:
    def test_extracts_tool_use_block(self):
        block = MagicMock()
        block.type = "tool_use"
        block.name = "submit_research_plan"
        block.input = {"steps": VALID_STEPS}
        message = MagicMock()
        message.content = [block]

        plan = extract_plan_from_anthropic_message(message)
        assert len(plan) == 3

    def test_raises_when_no_tool_block(self):
        message = MagicMock()
        message.content = [MagicMock(type="text", text="hello")]
        with pytest.raises(RuntimeError, match="tool_use"):
            extract_plan_from_anthropic_message(message)


class TestGetProvider:
    @patch("llm.factory.get_llm_provider_name", return_value=LLMProviderName.ANTHROPIC)
    @patch("llm.anthropic_provider.get_anthropic_api_key", return_value="sk-test")
    def test_returns_anthropic_provider(self, _mock_key, _mock_name):
        provider = get_provider("anthropic", api_key="sk-test")
        assert isinstance(provider, AnthropicProvider)

    @patch("llm.factory.get_llm_provider_name", return_value=LLMProviderName.OPENAI)
    @patch("llm.openai_provider.get_openai_api_key", return_value="sk-test")
    @patch("llm.openai_provider.get_openai_base_url", return_value="http://localhost/v1")
    def test_returns_openai_provider(self, _mock_url, _mock_key, _mock_name):
        provider = get_provider("openai", api_key="sk-test", base_url="http://localhost/v1")
        assert isinstance(provider, OpenAICompatibleProvider)

    def test_raises_on_unsupported_provider_string(self):
        from config import resolve_provider_name

        with pytest.raises(ConfigError):
            resolve_provider_name("unsupported")


class TestAnthropicProviderComplete:
    @patch("llm.anthropic_provider.anthropic.Anthropic")
    def test_complete_returns_result(self, mock_cls):
        block = MagicMock()
        block.type = "text"
        block.text = "Analysis output"
        message = MagicMock()
        message.content = [block]
        message.model = "claude-sonnet-4-6"
        message.usage.input_tokens = 10
        message.usage.output_tokens = 20

        mock_client = MagicMock()
        mock_client.messages.create.return_value = message
        mock_cls.return_value = mock_client

        provider = AnthropicProvider(api_key="sk-test")
        result = provider.complete(
            system="sys",
            user="user",
            model="claude-sonnet-4-6",
            max_tokens=100,
        )

        assert isinstance(result, CompletionResult)
        assert result.text == "Analysis output"


class TestOpenAIProviderComplete:
    @patch("llm.openai_provider.OpenAI")
    def test_complete_returns_result(self, mock_cls):
        choice = MagicMock()
        choice.message.content = "Report text"
        response = MagicMock()
        response.choices = [choice]
        response.model = "llama3.3"
        response.usage.prompt_tokens = 5
        response.usage.completion_tokens = 15

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = response
        mock_cls.return_value = mock_client

        provider = OpenAICompatibleProvider(
            api_key="sk-test", base_url="http://localhost/v1"
        )
        result = provider.complete(
            system="sys",
            user="user",
            model="llama3.3",
            max_tokens=100,
        )

        assert result.text == "Report text"
        assert result.output_tokens == 15

    @patch("llm.openai_provider.OpenAI")
    def test_create_plan_json_parses_steps(self, mock_cls):
        choice = MagicMock()
        choice.message.content = json.dumps({"steps": VALID_STEPS})
        response = MagicMock()
        response.choices = [choice]
        response.model = "llama3.3"
        response.usage.prompt_tokens = 5
        response.usage.completion_tokens = 50

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = response
        mock_cls.return_value = mock_client

        provider = OpenAICompatibleProvider(
            api_key="sk-test", base_url="http://localhost/v1"
        )
        plan = provider.create_plan_json(
            system="sys",
            user="plan",
            model="llama3.3",
            max_tokens=500,
        )
        assert len(plan) == 3
