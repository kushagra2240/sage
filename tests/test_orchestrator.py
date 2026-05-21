"""Tests for agents.orchestrator."""

from unittest.mock import patch

import pytest

from agents.orchestrator import run_research_pipeline


MOCK_RESEARCH = {
    "query": "climate policy",
    "system_prompt": "research prompt",
    "user_prompt": "user prompt",
    "results": [],
    "context": "formatted search context",
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


class TestRunResearchPipeline:
    @patch("agents.orchestrator.write_report", return_value=MOCK_REPORT)
    @patch("agents.orchestrator.analyze_findings", return_value=MOCK_ANALYSIS)
    @patch("agents.orchestrator.conduct_research", return_value=MOCK_RESEARCH)
    def test_runs_full_pipeline(self, mock_research, mock_analyze, mock_write):
        result = run_research_pipeline(
            "climate policy", audience="policy makers", max_results=4
        )

        assert result["query"] == "climate policy"
        assert result["research"] == MOCK_RESEARCH
        assert result["analysis"] == MOCK_ANALYSIS
        assert result["report"] == MOCK_REPORT
        assert result["orchestrator_prompt"]

        mock_research.assert_called_once_with("climate policy", max_results=4)
        mock_analyze.assert_called_once_with("formatted search context")
        mock_write.assert_called_once_with(
            "Structured analysis output.", audience="policy makers"
        )

    def test_raises_on_empty_query(self):
        with pytest.raises(ValueError, match="non-empty"):
            run_research_pipeline("")

    @patch("agents.orchestrator.conduct_research")
    def test_propagates_research_stage_errors(self, mock_research):
        mock_research.side_effect = ValueError("query must be a non-empty string")

        with pytest.raises(ValueError):
            run_research_pipeline("valid")
