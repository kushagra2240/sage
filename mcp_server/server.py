"""FastMCP server exposing Sage research tools."""

from fastmcp import FastMCP

from mcp_server.tools.search import format_search_results, search_web

mcp = FastMCP("Sage Research Assistant")


@mcp.tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for information on a topic using Tavily."""
    results = search_web(query, max_results=max_results)
    return format_search_results(results)


if __name__ == "__main__":
    mcp.run()
