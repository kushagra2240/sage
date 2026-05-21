"""Orchestrator: coordinates the research → analysis → writing pipeline."""

from typing import Any

from agents.analyst import analyze_findings
from agents.researcher import conduct_research
from agents.writer import write_report
from skills.prompts import ORCHESTRATOR_PROMPT


def run_research_pipeline(
    query: str,
    audience: str = "general",
    max_results: int = 5,
) -> dict[str, Any]:
    """
    Run the full multi-agent research pipeline for a query.

    Stages: research → analysis → report writing.
    """
    if not query or not query.strip():
        raise ValueError("query must be a non-empty string")

    research = conduct_research(query.strip(), max_results=max_results)
    analysis_result = analyze_findings(research["context"])
    report_result = write_report(analysis_result["analysis"], audience=audience)

    return {
        "query": query.strip(),
        "orchestrator_prompt": ORCHESTRATOR_PROMPT,
        "research": research,
        "analysis": analysis_result,
        "report": report_result,
    }
