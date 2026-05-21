"""Analyst agent: synthesizes research findings with Claude."""

from typing import Any

import anthropic

from config import get_anthropic_api_key
from skills.prompts import ANALYST_PROMPT, format_analysis_prompt

DEFAULT_MODEL = "claude-sonnet-4-20250514"


def _create_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=get_anthropic_api_key())


def analyze_findings(
    findings: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """
    Analyze research findings using the Anthropic API.

    Returns dict with keys: analysis, model, usage.
    """
    if not findings or not findings.strip():
        raise ValueError("findings must be a non-empty string")

    client = _create_client()
    user_prompt = format_analysis_prompt(findings.strip())

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=ANALYST_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text_blocks = [
        block.text for block in message.content if block.type == "text"
    ]
    analysis = "\n".join(text_blocks)

    return {
        "analysis": analysis,
        "model": message.model,
        "usage": {
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens,
        },
    }
