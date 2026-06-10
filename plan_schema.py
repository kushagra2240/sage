"""Research plan validation shared by agents and LLM planning.

Lives outside both ``agents`` and ``llm`` so neither package depends on
the other (avoids a circular import: llm.planning -> agents -> llm).
"""

from __future__ import annotations

from typing import Any

MIN_PLAN_STEPS = 3
MAX_PLAN_STEPS = 5


def validate_plan(plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ensure the orchestrator plan has 3-5 steps with required fields."""
    if not plan:
        raise ValueError("plan must contain at least one step")
    if len(plan) < MIN_PLAN_STEPS or len(plan) > MAX_PLAN_STEPS:
        raise ValueError(
            f"plan must have between {MIN_PLAN_STEPS} and {MAX_PLAN_STEPS} steps"
        )

    validated: list[dict[str, Any]] = []
    for item in plan:
        query = (item.get("search_query") or item.get("query") or "").strip()
        if not query:
            raise ValueError("each plan step must include a search_query")
        validated.append(
            {
                "step": item.get("step", len(validated) + 1),
                "search_query": query,
                "goal": (item.get("goal") or item.get("rationale") or "").strip(),
            }
        )
    return validated
