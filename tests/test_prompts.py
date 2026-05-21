"""Tests for skills.prompts."""

from skills.prompts import (
    format_analysis_prompt,
    format_research_prompt,
    format_writing_prompt,
)


class TestFormatResearchPrompt:
    def test_includes_query_and_context(self):
        result = format_research_prompt("AI safety", "result context here")
        assert "AI safety" in result
        assert "result context here" in result
        assert "Research topic" in result

    def test_handles_empty_context(self):
        result = format_research_prompt("topic", "")
        assert "topic" in result


class TestFormatAnalysisPrompt:
    def test_includes_findings(self):
        result = format_analysis_prompt("finding one\nfinding two")
        assert "finding one" in result
        assert "Analyze" in result


class TestFormatWritingPrompt:
    def test_includes_analysis_and_audience(self):
        result = format_writing_prompt("analysis text", audience="technical")
        assert "analysis text" in result
        assert "technical" in result

    def test_default_audience(self):
        result = format_writing_prompt("analysis")
        assert "general" in result
