"""Orchestrator: plans research and coordinates the agent pipeline."""

from __future__ import annotations

from typing import Any

from agents.analyst import analyze_findings
from agents.researcher import Researcher
from agents.writer import write_report
from config import LLMProviderName, get_default_model, resolve_provider_name
from llm import LLMProvider, get_provider
from llm.planning import (
    build_json_planning_user_message,
    build_planning_user_message,
)
from skills.prompts import ORCHESTRATOR_PROMPT


class Orchestrator:
    """
    Coordinates multi-agent research using a configurable LLM for planning.

    Anthropic: tool_use for structured plans. OpenAI-compatible: JSON fallback.
    Then runs Researcher → Analyst → Writer sequentially.
    """

    def __init__(
        self,
        model: str | None = None,
        researcher: Researcher | None = None,
        provider: LLMProvider | str | LLMProviderName | None = None,
    ) -> None:
        self._provider_name = resolve_provider_name(provider)
        self._provider = get_provider(self._provider_name)
        self.model = model or get_default_model(self._provider_name)
        self.researcher = researcher or Researcher()

    @property
    def provider(self) -> LLMProvider:
        return self._provider

    @property
    def provider_name(self) -> str:
        return self._provider_name.value

    def create_plan(self, question: str, max_tokens: int = 1024) -> list[dict[str, Any]]:
        """
        Generate a 3-5 step research strategy using the configured LLM.

        Args:
            question: The research question or topic.
            max_tokens: Token limit for the planning response.

        Returns:
            Validated list of plan step dicts.
        """
        if not question or not question.strip():
            raise ValueError("question must be a non-empty string")

        if self._provider.name == "anthropic":
            return self._provider.create_plan_with_tools(  # type: ignore[attr-defined]
                system=ORCHESTRATOR_PROMPT,
                user=build_planning_user_message(question),
                model=self.model,
                max_tokens=max_tokens,
            )

        if self._provider.name == "openai":
            return self._provider.create_plan_json(  # type: ignore[attr-defined]
                system=ORCHESTRATOR_PROMPT,
                user=build_json_planning_user_message(question),
                model=self.model,
                max_tokens=max_tokens,
            )

        raise RuntimeError(f"Unsupported provider for planning: {self._provider.name}")

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
        analysis_result = analyze_findings(
            research["context"],
            model=self.model,
            provider=self._provider,
        )
        report_result = write_report(
            analysis_result["analysis"],
            audience=audience,
            model=self.model,
            provider=self._provider,
        )

        return {
            "query": question.strip(),
            "provider": self.provider_name,
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
    provider: str | LLMProviderName | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Run the full multi-agent research pipeline for a query.

    Backward-compatible entry point delegating to Orchestrator.
    """
    _ = max_results  # retained for CLI compatibility; Researcher uses its own default
    return Orchestrator(provider=provider, model=model).run(query, audience=audience)
