"""Tests for agents.analyst."""

from unittest.mock import MagicMock, patch

import pytest

from agents.analyst import analyze_findings
from llm.base import CompletionResult


def _mock_completion(text: str = "Key themes: A, B, C.") -> CompletionResult:
    return CompletionResult(
        text=text,
        model="test-model",
        input_tokens=100,
        output_tokens=50,
    )


class TestAnalyzeFindings:
    @patch("agents.analyst.get_default_provider")
    def test_returns_analysis_on_success(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.complete.return_value = _mock_completion()
        mock_get_provider.return_value = mock_provider

        result = analyze_findings("Raw research findings here.")

        assert result["analysis"] == "Key themes: A, B, C."
        assert result["model"] == "test-model"
        assert result["usage"]["output_tokens"] == 50
        mock_provider.complete.assert_called_once()

    def test_raises_on_empty_findings(self):
        with pytest.raises(ValueError, match="non-empty"):
            analyze_findings("")

    @patch("agents.analyst.get_default_provider")
    def test_propagates_provider_errors(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.complete.side_effect = Exception("API rate limit")
        mock_get_provider.return_value = mock_provider

        with pytest.raises(Exception, match="rate limit"):
            analyze_findings("Some findings to analyze.")
