"""Writer agent: produces the final report with an LLM."""

from typing import Any

from config import get_default_model
from llm import LLMProvider, get_default_provider
from llm.base import CompletionResult
from skills.prompts import WRITER_PROMPT, format_writing_prompt


def _result_to_dict(result: CompletionResult) -> dict[str, Any]:
    return {
        "report": result.text,
        "model": result.model,
        "usage": {
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
        },
    }


def write_report(
    analysis: str,
    audience: str = "general",
    model: str | None = None,
    max_tokens: int = 4096,
    provider: LLMProvider | None = None,
) -> dict[str, Any]:
    """
    Write a research report from analyzed findings using the configured LLM.

    Returns dict with keys: report, model, usage.
    """
    if not analysis or not analysis.strip():
        raise ValueError("analysis must be a non-empty string")

    llm = provider or get_default_provider()
    resolved_model = model or get_default_model()

    result = llm.complete(
        system=WRITER_PROMPT,
        user=format_writing_prompt(analysis.strip(), audience=audience),
        model=resolved_model,
        max_tokens=max_tokens,
    )
    return _result_to_dict(result)
