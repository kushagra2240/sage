"""Web search tool backed by Tavily."""

from typing import Any

from tavily import TavilyClient

from config import get_tavily_api_key


def search_web(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Search the web via Tavily and return normalized result dicts.

    Each result contains: title, url, snippet.
    """
    if not query or not query.strip():
        raise ValueError("query must be a non-empty string")
    if max_results < 1:
        raise ValueError("max_results must be at least 1")

    client = TavilyClient(api_key=get_tavily_api_key())
    response = client.search(query=query.strip(), max_results=max_results)

    results = response.get("results", [])
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", ""),
        }
        for item in results
    ]


def format_search_results(results: list[dict[str, Any]]) -> str:
    """Format search results as plain text for agent consumption."""
    if not results:
        return "No results found."

    parts: list[str] = []
    for i, item in enumerate(results, start=1):
        parts.append(
            f"[{i}] {item.get('title', 'Untitled')}\n"
            f"URL: {item.get('url', '')}\n"
            f"{item.get('snippet', '')}"
        )
    return "\n\n".join(parts)
