"""Research agent: gathers information via MCP sage-tools."""

from __future__ import annotations

import asyncio
import re
from typing import Any

from mcp import ClientSession, StdioServerParameters

from agents.mcp_client import (
    get_server_params,
    parse_tool_result,
    run_with_session,
)
from plan_schema import (  # noqa: F401 — re-exported for backward compatibility
    MAX_PLAN_STEPS,
    MIN_PLAN_STEPS,
    validate_plan,
)
from skills.prompts import RESEARCHER_PROMPT, format_research_prompt


def _slugify(text: str, max_length: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_length] or "query"


class Researcher:
    """
    Research agent that uses MCP tools to search, extract, and save notes.

    Connects to the local sage-tools server via stdio and executes each
    step in the orchestrator's research plan.
    """

    def __init__(
        self,
        server_params: StdioServerParameters | None = None,
        top_urls_per_search: int = 2,
        max_search_results: int = 3,
    ) -> None:
        self._server_params = server_params or get_server_params()
        self.top_urls_per_search = top_urls_per_search
        self.max_search_results = max_search_results

    async def _call_tool(
        self,
        session: ClientSession,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Call a single MCP tool and parse the result."""
        result = await session.call_tool(name, arguments=arguments)
        return parse_tool_result(result)

    async def _execute_step(
        self,
        session: ClientSession,
        step: dict[str, Any],
    ) -> dict[str, Any]:
        """Run web_search, extract top URLs, and save a note for one plan step."""
        step_num = step["step"]
        query = step["search_query"]

        search_results = await self._call_tool(
            session,
            "web_search",
            {"query": query, "max_results": self.max_search_results},
        )
        if not isinstance(search_results, list):
            raise RuntimeError(f"web_search returned unexpected type for step {step_num}")

        extractions: list[dict[str, str]] = []
        for result in search_results[: self.top_urls_per_search]:
            url = result.get("url", "")
            if not url:
                continue
            try:
                content = await self._call_tool(
                    session, "extract_content", {"url": url}
                )
                extractions.append(
                    {
                        "url": url,
                        "title": result.get("title", ""),
                        "content": str(content) if content else "",
                    }
                )
            except RuntimeError:
                extractions.append(
                    {
                        "url": url,
                        "title": result.get("title", ""),
                        "content": result.get("snippet", ""),
                    }
                )

        note_body = _format_step_notes(step, search_results, extractions)
        note_key = f"step-{step_num}-{_slugify(query)}"
        save_confirmation = await self._call_tool(
            session,
            "save_note",
            {"key": note_key, "content": note_body},
        )

        return {
            "step": step_num,
            "search_query": query,
            "goal": step.get("goal", ""),
            "search_results": search_results,
            "extractions": extractions,
            "note_key": note_key,
            "save_confirmation": save_confirmation,
        }

    async def execute_plan(self, plan: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Execute a 3-5 step research plan using MCP tools.

        For each step: web_search → extract_content (top URLs) → save_note.
        """
        validated_plan = validate_plan(plan)

        async def _run(session: ClientSession) -> dict[str, Any]:
            step_results: list[dict[str, Any]] = []
            for step in validated_plan:
                step_results.append(await self._execute_step(session, step))

            context = _format_research_context(step_results)
            queries = [s["search_query"] for s in validated_plan]
            user_prompt = format_research_prompt(
                "; ".join(queries[:2]),
                context,
            )

            return {
                "plan": validated_plan,
                "steps": step_results,
                "context": context,
                "system_prompt": RESEARCHER_PROMPT,
                "user_prompt": user_prompt,
            }

        return await run_with_session(self._server_params, _run)

    def run_plan(self, plan: list[dict[str, Any]]) -> dict[str, Any]:
        """Synchronous wrapper around execute_plan."""
        return asyncio.run(self.execute_plan(plan))


def _format_step_notes(
    step: dict[str, Any],
    search_results: list[dict[str, Any]],
    extractions: list[dict[str, str]],
) -> str:
    lines = [
        f"## Step {step['step']}: {step['search_query']}",
        f"Goal: {step.get('goal', '')}",
        "",
        "### Search results",
    ]
    for i, hit in enumerate(search_results, start=1):
        lines.append(
            f"{i}. {hit.get('title', 'Untitled')} — {hit.get('url', '')}\n"
            f"   {hit.get('snippet', '')}"
        )
    lines.append("\n### Extracted content")
    for ext in extractions:
        preview = ext["content"][:500]
        lines.append(f"- {ext['title']} ({ext['url']})\n  {preview}")
    return "\n".join(lines)


def _format_research_context(step_results: list[dict[str, Any]]) -> str:
    parts = []
    for step in step_results:
        parts.append(
            f"### Step {step['step']}: {step['search_query']}\n"
            f"Note key: {step['note_key']}\n"
            f"Sources: {len(step['search_results'])} search hits, "
            f"{len(step['extractions'])} extractions"
        )
        for ext in step["extractions"]:
            preview = ext["content"][:300]
            parts.append(f"- {ext['title']}: {preview}")
    return "\n\n".join(parts)


def conduct_research(
    plan: list[dict[str, Any]],
    researcher: Researcher | None = None,
) -> dict[str, Any]:
    """
    Run research for an orchestrator plan via the Researcher agent.

    Prefer Orchestrator.run() for the full pipeline; this executes research only.
    """
    agent = researcher or Researcher()
    return agent.run_plan(plan)
