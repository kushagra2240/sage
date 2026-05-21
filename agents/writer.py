"""Writer agent: produces the final report with Claude."""

from typing import Any

import anthropic

from config import get_anthropic_api_key
from skills.prompts import WRITER_PROMPT, format_writing_prompt

DEFAULT_MODEL = "claude-sonnet-4-20250514"


def _create_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=get_anthropic_api_key())


def write_report(
    analysis: str,
    audience: str = "general",
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4096,
) -> dict[str, Any]:
    """
    Write a research report from analyzed findings using the Anthropic API.

    Returns dict with keys: report, model, usage.
    """
    if not analysis or not analysis.strip():
        raise ValueError("analysis must be a non-empty string")

    client = _create_client()
    user_prompt = format_writing_prompt(analysis.strip(), audience=audience)

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=WRITER_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text_blocks = [
        block.text for block in message.content if block.type == "text"
    ]
    report = "\n".join(text_blocks)

    return {
        "report": report,
        "model": message.model,
        "usage": {
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens,
        },
    }
