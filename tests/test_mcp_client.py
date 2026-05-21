"""Tests for agents.mcp_client helpers."""

import json
from unittest.mock import MagicMock

import pytest
from mcp.types import CallToolResult, TextContent

from agents.mcp_client import get_server_params, parse_tool_result


class TestGetServerParams:
    def test_uses_python_and_server_script(self):
        params = get_server_params()
        assert params.command
        assert any("server.py" in arg for arg in params.args)


class TestParseToolResult:
    def test_parses_json_list(self):
        payload = [{"title": "A", "url": "https://a.com", "snippet": "text"}]
        result = CallToolResult(
            content=[TextContent(type="text", text=json.dumps(payload))],
            isError=False,
        )
        assert parse_tool_result(result) == payload

    def test_returns_plain_text_when_not_json(self):
        result = CallToolResult(
            content=[TextContent(type="text", text="Note saved.")],
            isError=False,
        )
        assert parse_tool_result(result) == "Note saved."

    def test_raises_on_error_result(self):
        result = CallToolResult(
            content=[TextContent(type="text", text="Tool failed")],
            isError=True,
        )
        with pytest.raises(RuntimeError, match="Tool failed"):
            parse_tool_result(result)
