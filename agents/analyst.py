"""Analyst agent: synthesizes research findings with an LLM."""

from typing import Any

from config import get_default_model
from llm import LLMProvider, get_default_provider
from llm.base import CompletionResult
from skills.prompts import ANALYST_PROMPT, format_analysis_prompt


def _result_to_dict(result: CompletionResult) -> dict[str, Any]:
    return {
        "analysis": result.text,
        "model": result.model,
        "usage": {
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
        },
    }


def analyze_findings(
    findings: str,
    model: str | None = None,
    max_tokens: int = 2048,
    provider: LLMProvider | None = None,
) -> dict[str, Any]:
    """
    Analyze research findings using the configured LLM provider.

    Returns dict with keys: analysis, model, usage.
    """
    if not findings or not findings.strip():
        raise ValueError("findings must be a non-empty string")

    llm = provider or get_default_provider()
    resolved_model = model or get_default_model()

    result = llm.complete(
        system=ANALYST_PROMPT,
        user=format_analysis_prompt(findings.strip()),
        model=resolved_model,
        max_tokens=max_tokens,
    )
    return _result_to_dict(result)
