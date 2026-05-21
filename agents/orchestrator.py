"""Orchestrator: plans research and coordinates the agent pipeline."""

from __future__ import annotations

import json
from typing import Any

import anthropic

from agents.analyst import analyze_findings
from agents.researcher import MIN_PLAN_STEPS, MAX_PLAN_STEPS, Researcher, validate_plan
from agents.writer import write_report
from config import get_anthropic_api_key
from skills.prompts import ORCHESTRATOR_PROMPT

DEFAULT_MODEL = "claude-sonnet-4-6"

PLAN_TOOL_NAME = "submit_research_plan"

PLAN_TOOL = {
    "name": PLAN_TOOL_NAME,
    "description": (
        "Submit a structured research plan with 3-5 steps. "
        "Each step must include a focused web search query."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "steps": {
                "type": "array",
                "description": "Ordered research steps (3 to 5).",
                "minItems": MIN_PLAN_STEPS,
                "maxItems": MAX_PLAN_STEPS,
                "items": {
                    "type": "object",
                    "properties": {
                        "step": {
                            "type": "integer",
                            "description": "Step number starting at 1",
                        },
                        "search_query": {
                            "type": "string",
                            "description": "Web search query for this step",
                        },
                        "goal": {
                            "type": "string",
                            "description": "What this step should uncover",
                        },
                    },
                    "required": ["step", "search_query", "goal"],
                },
            }
        },
        "required": ["steps"],
    },
}


def _create_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=get_anthropic_api_key())


def _extract_plan_from_message(message: anthropic.types.Message) -> list[dict[str, Any]]:
    """Parse the tool_use block containing the research plan."""
    for block in message.content:
        if block.type == "tool_use" and block.name == PLAN_TOOL_NAME:
            steps = block.input.get("steps", [])
            return validate_plan(steps)

    raise RuntimeError("Model did not return a research plan via tool_use")


class Orchestrator:
    """
    Coordinates multi-agent research using Claude for planning.

    Uses tool_use to produce a 3-5 step strategy, then runs Researcher →
    Analyst → Writer sequentially, passing outputs between stages.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        researcher: Researcher | None = None,
    ) -> None:
        self.model = model
        self.researcher = researcher or Researcher()

    def create_plan(self, question: str, max_tokens: int = 1024) -> list[dict[str, Any]]:
        """
        Use Claude with tool_use to generate a 3-5 step research strategy.

        Args:
            question: The research question or topic.
            max_tokens: Token limit for the planning response.

        Returns:
            Validated list of plan step dicts.
        """
        if not question or not question.strip():
            raise ValueError("question must be a non-empty string")

        client = _create_client()
        message = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=ORCHESTRATOR_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Research question: {question.strip()}\n\n"
                        "Create a research plan with 3-5 steps. Each step needs "
                        "a specific web search query and a clear goal."
                    ),
                }
            ],
            tools=[PLAN_TOOL],
            tool_choice={"type": "tool", "name": PLAN_TOOL_NAME},
        )

        return _extract_plan_from_message(message)

    def run(
        self,
        question: str,
        audience: str = "general",
    ) -> dict[str, Any]:
        """
        Run the full pipeline: plan → research → analyze → write.

        Returns a dict with plan, research, analysis, and report stages.
        """
        if not question or not question.strip():
            raise ValueError("question must be a non-empty string")

        plan = self.create_plan(question)
        research = self.researcher.run_plan(plan)
        analysis_result = analyze_findings(research["context"])
        report_result = write_report(
            analysis_result["analysis"],
            audience=audience,
        )

        return {
            "query": question.strip(),
            "model": self.model,
            "orchestrator_prompt": ORCHESTRATOR_PROMPT,
            "plan": plan,
            "research": research,
            "analysis": analysis_result,
            "report": report_result,
        }


def run_research_pipeline(
    query: str,
    audience: str = "general",
    max_results: int = 5,
) -> dict[str, Any]:
    """
    Run the full multi-agent research pipeline for a query.

    Backward-compatible entry point delegating to Orchestrator.
    """
    _ = max_results  # retained for CLI compatibility; Researcher uses its own default
    return Orchestrator().run(query, audience=audience)
