"""Tests for mcp_server.tools.search."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_server.tools.search import format_search_results, search_web


SAMPLE_TAVILY_RESPONSE = {
    "results": [
        {
            "title": "Example Article",
            "url": "https://example.com/article",
            "content": "Sample content about the topic.",
            "score": 0.95,
        },
        {
            "title": "Second Source",
            "url": "https://example.com/second",
            "content": "More information.",
            "score": 0.80,
        },
    ]
}


class TestSearchWeb:
    @patch("mcp_server.tools.search.get_tavily_api_key", return_value="tvly-test")
    @patch("mcp_server.tools.search.TavilyClient")
    def test_returns_normalized_results(self, mock_client_cls, _mock_key):
        mock_client = MagicMock()
        mock_client.search.return_value = SAMPLE_TAVILY_RESPONSE
        mock_client_cls.return_value = mock_client

        results = search_web("quantum computing", max_results=3)

        assert len(results) == 2
        assert results[0]["title"] == "Example Article"
        assert results[0]["url"] == "https://example.com/article"
        assert results[0]["score"] == 0.95
        mock_client.search.assert_called_once_with(
            query="quantum computing", max_results=3
        )

    @patch("mcp_server.tools.search.get_tavily_api_key", return_value="tvly-test")
    @patch("mcp_server.tools.search.TavilyClient")
    def test_strips_query_whitespace(self, mock_client_cls, _mock_key):
        mock_client = MagicMock()
        mock_client.search.return_value = {"results": []}
        mock_client_cls.return_value = mock_client

        search_web("  spaced query  ")

        mock_client.search.assert_called_once_with(
            query="spaced query", max_results=5
        )

    def test_raises_on_empty_query(self):
        with pytest.raises(ValueError, match="non-empty"):
            search_web("")

    def test_raises_on_invalid_max_results(self):
        with pytest.raises(ValueError, match="max_results"):
            search_web("valid query", max_results=0)

    @patch("mcp_server.tools.search.get_tavily_api_key")
    @patch("mcp_server.tools.search.TavilyClient")
    def test_propagates_api_errors(self, mock_client_cls, mock_get_key):
        from config import ConfigError

        mock_get_key.side_effect = ConfigError("TAVILY_API_KEY is not set")

        with pytest.raises(ConfigError):
            search_web("any query")


class TestFormatSearchResults:
    def test_formats_multiple_results(self):
        results = [
            {"title": "A", "url": "https://a.com", "content": "Content A"},
            {"title": "B", "url": "https://b.com", "content": "Content B"},
        ]
        text = format_search_results(results)
        assert "[1] A" in text
        assert "[2] B" in text
        assert "https://a.com" in text

    def test_empty_results_message(self):
        assert format_search_results([]) == "No results found."
