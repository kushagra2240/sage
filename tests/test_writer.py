"""Tests for agents.writer."""

from unittest.mock import MagicMock, patch

import pytest

from agents.writer import write_report
from llm.base import CompletionResult


def _mock_completion(text: str = "# Final Report\n\nSummary.") -> CompletionResult:
    return CompletionResult(
        text=text,
        model="test-model",
        input_tokens=200,
        output_tokens=800,
    )


class TestWriteReport:
    @patch("agents.writer.get_default_provider")
    def test_returns_report_on_success(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.complete.return_value = _mock_completion()
        mock_get_provider.return_value = mock_provider

        result = write_report("Analysis with insights.", audience="executive")

        assert "Final Report" in result["report"]
        assert result["usage"]["output_tokens"] == 800
        call_kwargs = mock_provider.complete.call_args.kwargs
        assert "executive" in call_kwargs["user"]

    def test_raises_on_empty_analysis(self):
        with pytest.raises(ValueError, match="non-empty"):
            write_report("")

    @patch("agents.writer.get_default_provider")
    def test_propagates_provider_errors(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.complete.side_effect = Exception("Authentication failed")
        mock_get_provider.return_value = mock_provider

        with pytest.raises(Exception, match="Authentication"):
            write_report("Valid analysis content.")
