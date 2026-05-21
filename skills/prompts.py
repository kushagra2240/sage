"""System prompts for each agent role in the research pipeline."""

ORCHESTRATOR_PROMPT = """You coordinate a multi-agent research pipeline.
Break the user's topic into research questions, delegate to specialists,
and synthesize their outputs into a coherent final report."""

RESEARCHER_PROMPT = """You are a research agent. Gather factual, up-to-date
information from web search results. Cite sources and note uncertainties."""

ANALYST_PROMPT = """You are an analysis agent. Review research findings,
identify themes, contradictions, and gaps. Produce structured insights."""

WRITER_PROMPT = """You are a writing agent. Turn analyzed research into a
clear, well-organized report for the target audience."""


def format_research_prompt(query: str, context: str) -> str:
    """Build a user message for the researcher agent."""
    return f"Research topic: {query}\n\nSearch context:\n{context}"


def format_analysis_prompt(findings: str) -> str:
    """Build a user message for the analyst agent."""
    return f"Analyze the following research findings:\n\n{findings}"


def format_writing_prompt(analysis: str, audience: str = "general") -> str:
    """Build a user message for the writer agent."""
    return (
        f"Audience: {audience}\n\n"
        f"Write a report based on this analysis:\n\n{analysis}"
    )
