"""Tests for mcp_server.tools.content."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from mcp_server.tools.content import extract_content

SAMPLE_HTML = """
<html><body>
<main>
  <h1>Report Title</h1>
  <p>Detailed analysis paragraph.</p>
</main>
<script>alert('x')</script>
</body></html>
"""


class TestExtractContentTool:
    @patch("mcp_server.tools.content.httpx.get")
    def test_extracts_text_from_main(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        text = extract_content("https://example.com/report")

        assert "Report Title" in text
        assert "Detailed analysis" in text
        assert "alert" not in text

    def test_raises_on_empty_url(self):
        with pytest.raises(ValueError, match="non-empty"):
            extract_content("")

    @patch("mcp_server.tools.content.httpx.get")
    def test_raises_on_request_error(self, mock_get):
        mock_get.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(RuntimeError, match="Failed to fetch"):
            extract_content("https://example.com/page")
