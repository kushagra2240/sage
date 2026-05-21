"""Tests for agents.writer."""

from unittest.mock import MagicMock, patch

import pytest

from agents.writer import write_report


def _mock_message(text: str, model: str = "claude-sonnet-4-20250514"):
    block = MagicMock()
    block.type = "text"
    block.text = text
    message = MagicMock()
    message.content = [block]
    message.model = model
    message.usage.input_tokens = 200
    message.usage.output_tokens = 800
    return message


class TestWriteReport:
    @patch("agents.writer._create_client")
    def test_returns_report_on_success(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_message(
            "# Final Report\n\nExecutive summary here."
        )
        mock_create_client.return_value = mock_client

        result = write_report("Analysis with insights.", audience="executive")

        assert "Final Report" in result["report"]
        assert result["usage"]["output_tokens"] == 800
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "executive" in call_kwargs["messages"][0]["content"]

    def test_raises_on_empty_analysis(self):
        with pytest.raises(ValueError, match="non-empty"):
            write_report("")

    @patch("agents.writer._create_client")
    def test_propagates_anthropic_api_errors(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("Authentication failed")
        mock_create_client.return_value = mock_client

        with pytest.raises(Exception, match="Authentication"):
            write_report("Valid analysis content.")
