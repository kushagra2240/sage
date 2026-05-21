"""Helpers for connecting to the Sage MCP server via the mcp Python SDK."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_server_params(
    env: dict[str, str] | None = None,
) -> StdioServerParameters:
    """
    Build stdio parameters to launch the local sage-tools MCP server.

    Uses ``python -m mcp_server`` from the project root so package
    imports resolve correctly (avoids ModuleNotFoundError).
    """
    # Ensure .env from project root is visible to the subprocess
    import config  # noqa: F401 — loads dotenv into os.environ

    server_env = {**os.environ}
    if env:
        server_env.update(env)

    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_server"],
        env=server_env,
        cwd=str(PROJECT_ROOT),
    )


def parse_tool_result(result: CallToolResult) -> Any:
    """
    Parse an MCP CallToolResult into Python data.

    Attempts JSON deserialization for structured tool outputs; otherwise
    returns concatenated text content.
    """
    if result.isError:
        message = _content_to_text(result.content) or "Unknown MCP tool error"
        raise RuntimeError(message)

    text = _content_to_text(result.content).strip()
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _content_to_text(content: list[Any]) -> str:
    parts: list[str] = []
    for block in content:
        if isinstance(block, TextContent):
            parts.append(block.text)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
        elif hasattr(block, "text"):
            parts.append(str(block.text))
    return "".join(parts)


async def run_with_session(
    server_params: StdioServerParameters,
    callback: Any,
) -> Any:
    """Open an MCP session, initialize it, and run an async callback."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await callback(session)
