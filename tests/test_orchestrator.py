"""Tests for agents.orchestrator."""

from unittest.mock import MagicMock, patch

import pytest

from agents.orchestrator import (
    Orchestrator,
    _extract_plan_from_message,
    run_research_pipeline,
)


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
    "model": "claude-sonnet-4-20250514",
    "usage": {"input_tokens": 10, "output_tokens": 20},
}

MOCK_REPORT = {
    "report": "Final written report.",
    "model": "claude-sonnet-4-20250514",
    "usage": {"input_tokens": 30, "output_tokens": 100},
}


def _mock_plan_message(steps: list[dict] | None = None):
    block = MagicMock()
    block.type = "tool_use"
    block.name = "submit_research_plan"
    block.input = {"steps": steps or VALID_PLAN}
    message = MagicMock()
    message.content = [block]
    return message


class TestExtractPlanFromMessage:
    def test_extracts_and_validates_steps(self):
        plan = _extract_plan_from_message(_mock_plan_message())
        assert len(plan) == 3
        assert plan[0]["search_query"] == "climate policy overview"

    def test_raises_when_no_tool_use_block(self):
        message = MagicMock()
        message.content = [MagicMock(type="text", text="no plan")]
        with pytest.raises(RuntimeError, match="did not return"):
            _extract_plan_from_message(message)


class TestOrchestratorCreatePlan:
    @patch("agents.orchestrator._create_client")
    def test_returns_validated_plan(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_plan_message()
        mock_create_client.return_value = mock_client

        orchestrator = Orchestrator()
        plan = orchestrator.create_plan("climate policy")

        assert len(plan) == 3
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-sonnet-4-6"
        assert call_kwargs["tool_choice"]["name"] == "submit_research_plan"

    def test_raises_on_empty_question(self):
        orchestrator = Orchestrator()
        with pytest.raises(ValueError, match="non-empty"):
            orchestrator.create_plan("")

    @patch("agents.orchestrator._create_client")
    def test_propagates_anthropic_api_errors(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API rate limit")
        mock_create_client.return_value = mock_client

        orchestrator = Orchestrator()
        with pytest.raises(Exception, match="rate limit"):
            orchestrator.create_plan("climate policy")


class TestOrchestratorRun:
    @patch("agents.orchestrator.write_report", return_value=MOCK_REPORT)
    @patch("agents.orchestrator.analyze_findings", return_value=MOCK_ANALYSIS)
    def test_runs_full_pipeline(self, mock_analyze, mock_write):
        mock_researcher = MagicMock()
        mock_researcher.run_plan.return_value = MOCK_RESEARCH

        orchestrator = Orchestrator(researcher=mock_researcher)
        with patch.object(
            orchestrator, "create_plan", return_value=VALID_PLAN
        ) as mock_plan:
            result = orchestrator.run(
                "climate policy", audience="policy makers"
            )

        assert result["query"] == "climate policy"
        assert result["plan"] == VALID_PLAN
        assert result["research"] == MOCK_RESEARCH
        assert result["analysis"] == MOCK_ANALYSIS
        assert result["report"] == MOCK_REPORT

        mock_plan.assert_called_once_with("climate policy")
        mock_researcher.run_plan.assert_called_once_with(VALID_PLAN)
        mock_analyze.assert_called_once_with(MOCK_RESEARCH["context"])
        mock_write.assert_called_once_with(
            "Structured analysis output.", audience="policy makers"
        )

    def test_raises_on_empty_question(self):
        orchestrator = Orchestrator(researcher=MagicMock())
        with pytest.raises(ValueError, match="non-empty"):
            orchestrator.run("")


class TestRunResearchPipeline:
    @patch("agents.orchestrator.Orchestrator")
    def test_delegates_to_orchestrator_class(self, mock_orch_cls):
        mock_instance = MagicMock()
        mock_instance.run.return_value = {"query": "topic", "report": MOCK_REPORT}
        mock_orch_cls.return_value = mock_instance

        result = run_research_pipeline("topic", audience="general")

        mock_orch_cls.assert_called_once()
        mock_instance.run.assert_called_once_with("topic", audience="general")
        assert result["query"] == "topic"
