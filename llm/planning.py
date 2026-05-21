"""Research plan schema and parsing for orchestrator planning."""

from __future__ import annotations

import json
import re
from typing import Any

from agents.researcher import MAX_PLAN_STEPS, MIN_PLAN_STEPS, validate_plan

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


def build_planning_user_message(question: str) -> str:
    """User message for research planning (tool_use or JSON)."""
    return (
        f"Research question: {question.strip()}\n\n"
        "Create a research plan with 3-5 steps. Each step needs "
        "a specific web search query and a clear goal."
    )


def build_json_planning_user_message(question: str) -> str:
    """User message when the model must return JSON only."""
    schema_hint = json.dumps(
        {
            "steps": [
                {
                    "step": 1,
                    "search_query": "example search query",
                    "goal": "what this step should uncover",
                }
            ]
        },
        indent=2,
    )
    return (
        f"{build_planning_user_message(question)}\n\n"
        "Respond with ONLY valid JSON matching this shape (3 to 5 steps in "
        f'"steps"):\n{schema_hint}'
    )


def parse_plan_from_json(text: str) -> list[dict[str, Any]]:
    """Parse and validate a research plan from model JSON output."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in research plan: {exc}") from exc

    if isinstance(data, list):
        steps = data
    elif isinstance(data, dict):
        steps = data.get("steps", [])
    else:
        raise RuntimeError("Research plan JSON must be an object with 'steps' or a list")

    return validate_plan(steps)


def extract_plan_from_anthropic_message(message: Any) -> list[dict[str, Any]]:
    """Parse the tool_use block containing the research plan."""
    for block in message.content:
        if block.type == "tool_use" and block.name == PLAN_TOOL_NAME:
            steps = block.input.get("steps", [])
            return validate_plan(steps)

    raise RuntimeError("Model did not return a research plan via tool_use")
