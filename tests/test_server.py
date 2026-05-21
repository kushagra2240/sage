"""Tests for mcp_server.server tools."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from config import ConfigError
from mcp_server.server import extract_content, save_note, web_search
from mcp_server.tools.notes import clear_notes


SAMPLE_TAVILY_RESPONSE = {
    "results": [
        {
            "title": "Example Article",
            "url": "https://example.com/article",
            "content": "Sample snippet about the topic.",
        },
    ]
}

SAMPLE_HTML = """
<html><body>
<article>
  <h1>Main Article</h1>
  <p>This is the primary content.</p>
</article>
<nav>Skip this</nav>
</body></html>
"""


@pytest.fixture(autouse=True)
def _clear_notes():
    clear_notes()
    yield
    clear_notes()


class TestWebSearch:
    @patch("mcp_server.tools.search.get_tavily_api_key", return_value="tvly-test")
    @patch("mcp_server.tools.search.TavilyClient")
    def test_returns_results_with_snippet(self, mock_client_cls, _mock_key):
        mock_client = MagicMock()
        mock_client.search.return_value = SAMPLE_TAVILY_RESPONSE
        mock_client_cls.return_value = mock_client

        results = web_search("quantum computing", max_results=3)

        assert len(results) == 1
        assert results[0] == {
            "title": "Example Article",
            "url": "https://example.com/article",
            "snippet": "Sample snippet about the topic.",
        }

    def test_raises_on_empty_query(self):
        with pytest.raises(ValueError, match="non-empty"):
            web_search("")

    @patch("mcp_server.tools.search.get_tavily_api_key")
    @patch("mcp_server.tools.search.TavilyClient")
    def test_raises_runtime_error_on_api_failure(
        self, mock_client_cls, mock_get_key
    ):
        mock_get_key.return_value = "tvly-test"
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("Service unavailable")
        mock_client_cls.return_value = mock_client

        with pytest.raises(RuntimeError, match="Tavily search failed"):
            web_search("valid query")


class TestExtractContent:
    @patch("mcp_server.tools.content.httpx.get")
    def test_extracts_main_text(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        text = extract_content("https://example.com/article")

        assert "Main Article" in text
        assert "primary content" in text
        assert "Skip this" not in text
        mock_get.assert_called_once()

    def test_raises_on_empty_url(self):
        with pytest.raises(ValueError, match="non-empty"):
            extract_content("")

    def test_raises_on_invalid_scheme(self):
        with pytest.raises(ValueError, match="http"):
            extract_content("ftp://example.com/file")

    @patch("mcp_server.tools.content.httpx.get")
    def test_raises_runtime_error_on_http_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        mock_get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=mock_response,
        )

        with pytest.raises(RuntimeError, match="Content extraction failed"):
            extract_content("https://example.com/missing")


class TestSaveNote:
    def test_saves_and_returns_confirmation(self):
        result = save_note("topic-summary", "Key findings here.")

        assert "topic-summary" in result
        assert "18 characters" in result

    def test_raises_on_empty_key(self):
        with pytest.raises(ValueError, match="non-empty"):
            save_note("", "some content")

    def test_raises_on_none_content(self):
        with pytest.raises(ValueError, match="None"):
            save_note("valid-key", None)  # type: ignore[arg-type]

    def test_overwrites_existing_note(self):
        save_note("draft", "version one")
        result = save_note("draft", "version two")

        assert "11 characters" in result
