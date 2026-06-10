"""Tests for agents.orchestrator."""

from unittest.mock import MagicMock, patch

import pytest

from agents.orchestrator import Orchestrator, run_research_pipeline

VALID_PLAN = [
    {"step": 1, "search_query": "climate policy overview", "goal": "Overview"},
    {"step": 2, "search_query": "carbon pricing mechanisms", "goal": "Pricing"},
    {"step": 3, "search_query": "renewable energy subsidies", "goal": "Subsidies"},
]

MOCK_RESEARCH = {
    "plan": VALID_PLAN,
    "context": "formatted search context from MCP tools",
    "steps": [],
    "system_prompt": "research prompt",
    "user_prompt": "user prompt",
}

MOCK_ANALYSIS = {
    "analysis": "Structured analysis output.",
    "model": "test-model",
    "usage": {"input_tokens": 10, "output_tokens": 20},
}

MOCK_REPORT = {
    "report": "Final written report.",
    "model": "test-model",
    "usage": {"input_tokens": 30, "output_tokens": 100},
}


class TestOrchestratorCreatePlan:
    def test_anthropic_uses_tool_planning(self):
        mock_provider = MagicMock()
        mock_provider.name = "anthropic"
        mock_provider.create_plan_with_tools.return_value = VALID_PLAN

        with patch("agents.orchestrator.get_provider", return_value=mock_provider):
            orchestrator = Orchestrator(provider="anthropic", model="claude-sonnet-4-6")
            plan = orchestrator.create_plan("climate policy")

        assert len(plan) == 3
        mock_provider.create_plan_with_tools.assert_called_once()

    def test_openai_uses_json_planning(self):
        mock_provider = MagicMock()
        mock_provider.name = "openai"
        mock_provider.create_plan_json.return_value = VALID_PLAN

        with patch("agents.orchestrator.get_provider", return_value=mock_provider):
            orchestrator = Orchestrator(provider="openai", model="llama3.3")
            plan = orchestrator.create_plan("climate policy")

        assert len(plan) == 3
        mock_provider.create_plan_json.assert_called_once()

    def test_raises_on_empty_question(self):
        with patch("agents.orchestrator.get_provider", return_value=MagicMock()):
            orchestrator = Orchestrator()
            with pytest.raises(ValueError, match="non-empty"):
                orchestrator.create_plan("")

    def test_propagates_planning_errors(self):
        mock_provider = MagicMock()
        mock_provider.name = "anthropic"
        mock_provider.create_plan_with_tools.side_effect = Exception("API rate limit")

        with patch("agents.orchestrator.get_provider", return_value=mock_provider):
            orchestrator = Orchestrator(provider="anthropic")
            with pytest.raises(Exception, match="rate limit"):
                orchestrator.create_plan("climate policy")


class TestOrchestratorRun:
    @patch("agents.orchestrator.write_report", return_value=MOCK_REPORT)
    @patch("agents.orchestrator.analyze_findings", return_value=MOCK_ANALYSIS)
    def test_runs_full_pipeline(self, mock_analyze, mock_write):
        mock_provider = MagicMock()
        mock_provider.name = "anthropic"
        mock_provider.create_plan_with_tools.return_value = VALID_PLAN

        mock_researcher = MagicMock()
        mock_researcher.run_plan.return_value = MOCK_RESEARCH

        with patch("agents.orchestrator.get_provider", return_value=mock_provider):
            orchestrator = Orchestrator(
                provider="anthropic",
                model="claude-sonnet-4-6",
                researcher=mock_researcher,
            )
            with patch.object(
                orchestrator, "create_plan", return_value=VALID_PLAN
            ) as mock_plan:
                result = orchestrator.run(
                    "climate policy", audience="policy makers"
                )

        assert result["query"] == "climate policy"
        assert result["plan"] == VALID_PLAN
        mock_plan.assert_called_once_with("climate policy")
        mock_researcher.run_plan.assert_called_once_with(VALID_PLAN)
        mock_analyze.assert_called_once()
        mock_write.assert_called_once()

    def test_raises_on_empty_question(self):
        with patch("agents.orchestrator.get_provider", return_value=MagicMock()):
            orchestrator = Orchestrator(researcher=MagicMock())
            with pytest.raises(ValueError, match="non-empty"):
                orchestrator.run("")


class TestRunResearchPipeline:
    @patch("agents.orchestrator.Orchestrator")
    def test_delegates_to_orchestrator_class(self, mock_orch_cls):
        mock_instance = MagicMock()
        mock_instance.run.return_value = {"query": "topic", "report": MOCK_REPORT}
        mock_orch_cls.return_value = mock_instance

        result = run_research_pipeline(
            "topic", audience="general", provider="openai", model="llama3.3"
        )

        mock_orch_cls.assert_called_once_with(provider="openai", model="llama3.3")
        mock_instance.run.assert_called_once_with("topic", audience="general")
        assert result["query"] == "topic"
