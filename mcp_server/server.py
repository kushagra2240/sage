"""FastMCP server exposing Sage research tools."""

from typing import Any

from fastmcp import FastMCP

from mcp_server.tools.content import extract_content as _extract_content
from mcp_server.tools.notes import save_note as _save_note
from mcp_server.tools.search import search_web as _search_web

mcp = FastMCP("sage-tools")


@mcp.tool
def web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Search the web using the Tavily API.

    Args:
        query: Search terms to look up.
        max_results: Maximum number of results to return (default 5).

    Returns:
        A list of dicts, each with keys: title, url, snippet.

    Raises:
        ValueError: If query is empty or max_results is invalid.
        ConfigError: If TAVILY_API_KEY is not configured.
        RuntimeError: If the Tavily API request fails.
    """
    if not query or not query.strip():
        raise ValueError("query must be a non-empty string")

    try:
        return _search_web(query.strip(), max_results=max_results)
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Tavily search failed: {exc}") from exc


@mcp.tool
def extract_content(url: str) -> str:
    """
    Fetch a URL and extract its main text content.

    Uses httpx for HTTP requests and BeautifulSoup to parse HTML,
    preferring <article> or <main> elements when present.

    Args:
        url: Fully qualified HTTP or HTTPS URL to fetch.

    Returns:
        Extracted plain-text content from the page.

    Raises:
        ValueError: If the URL is empty or malformed.
        RuntimeError: If the request fails or no content can be extracted.
    """
    if not url or not url.strip():
        raise ValueError("url must be a non-empty string")

    try:
        return _extract_content(url.strip())
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Content extraction failed: {exc}") from exc


@mcp.tool
def save_note(key: str, content: str) -> str:
    """
    Store a text note in an in-memory dictionary.

    Args:
        key: Unique identifier for the note.
        content: Text content to store (may be empty string).

    Returns:
        Confirmation message with the key and content length.

    Raises:
        ValueError: If key is empty or content is None.
    """
    if not key or not key.strip():
        raise ValueError("key must be a non-empty string")
    if content is None:
        raise ValueError("content must not be None")

    try:
        return _save_note(key.strip(), content)
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Failed to save note: {exc}") from exc


if __name__ == "__main__":
    mcp.run()
