"""Tests for agents.researcher."""

from unittest.mock import patch

import pytest

from agents.researcher import conduct_research


MOCK_RESULTS = [
    {
        "title": "Test Source",
        "url": "https://test.example",
        "snippet": "Relevant information.",
    }
]


class TestConductResearch:
    @patch("agents.researcher.search_web", return_value=MOCK_RESULTS)
    def test_returns_structured_findings(self, mock_search):
        result = conduct_research("renewable energy", max_results=3)

        assert result["query"] == "renewable energy"
        assert result["results"] == MOCK_RESULTS
        assert "renewable energy" in result["user_prompt"]
        assert "Test Source" in result["context"]
        assert result["system_prompt"]
        mock_search.assert_called_once_with("renewable energy", max_results=3)

    @patch("agents.researcher.search_web", return_value=MOCK_RESULTS)
    def test_strips_query_whitespace(self, mock_search):
        conduct_research("  trimmed topic  ")
        mock_search.assert_called_once_with("trimmed topic", max_results=5)

    def test_raises_on_empty_query(self):
        with pytest.raises(ValueError, match="non-empty"):
            conduct_research("")

    @patch("agents.researcher.search_web")
    def test_propagates_search_errors(self, mock_search):
        mock_search.side_effect = RuntimeError("Tavily API unavailable")

        with pytest.raises(RuntimeError, match="Tavily"):
            conduct_research("valid query")
