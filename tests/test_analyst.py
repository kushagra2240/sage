"""Tests for agents.analyst."""

from unittest.mock import MagicMock, patch

import pytest

from agents.analyst import analyze_findings


def _mock_message(text: str, model: str = "claude-sonnet-4-20250514"):
    block = MagicMock()
    block.type = "text"
    block.text = text
    message = MagicMock()
    message.content = [block]
    message.model = model
    message.usage.input_tokens = 100
    message.usage.output_tokens = 50
    return message


class TestAnalyzeFindings:
    @patch("agents.analyst._create_client")
    def test_returns_analysis_on_success(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_message(
            "Key themes: A, B, C."
        )
        mock_create_client.return_value = mock_client

        result = analyze_findings("Raw research findings here.")

        assert result["analysis"] == "Key themes: A, B, C."
        assert result["model"] == "claude-sonnet-4-20250514"
        assert result["usage"]["input_tokens"] == 100
        assert result["usage"]["output_tokens"] == 50
        mock_client.messages.create.assert_called_once()

    def test_raises_on_empty_findings(self):
        with pytest.raises(ValueError, match="non-empty"):
            analyze_findings("")

    @patch("agents.analyst._create_client")
    def test_propagates_anthropic_api_errors(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API rate limit")
        mock_create_client.return_value = mock_client

        with pytest.raises(Exception, match="rate limit"):
            analyze_findings("Some findings to analyze.")
