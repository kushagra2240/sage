"""Research agent: gathers information via web search."""

from typing import Any

from mcp_server.tools.search import format_search_results, search_web
from skills.prompts import RESEARCHER_PROMPT, format_research_prompt


def conduct_research(query: str, max_results: int = 5) -> dict[str, Any]:
    """
    Run web research for a query and return structured findings.

    Returns dict with keys: query, system_prompt, user_prompt, results, context.
    """
    if not query or not query.strip():
        raise ValueError("query must be a non-empty string")

    results = search_web(query.strip(), max_results=max_results)
    context = format_search_results(results)
    user_prompt = format_research_prompt(query.strip(), context)

    return {
        "query": query.strip(),
        "system_prompt": RESEARCHER_PROMPT,
        "user_prompt": user_prompt,
        "results": results,
        "context": context,
    }
