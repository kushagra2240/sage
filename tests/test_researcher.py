"""Tests for agents.researcher."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.researcher import (
    Researcher,
    conduct_research,
    validate_plan,
)

VALID_PLAN = [
    {"step": 1, "search_query": "renewable energy trends 2025", "goal": "Trends"},
    {"step": 2, "search_query": "solar capacity growth", "goal": "Solar data"},
    {"step": 3, "search_query": "wind power adoption", "goal": "Wind data"},
]

MOCK_SEARCH_RESULTS = [
    {
        "title": "Test Source",
        "url": "https://test.example/article",
        "snippet": "Relevant information.",
    }
]


class TestValidatePlan:
    def test_accepts_valid_plan(self):
        plan = validate_plan(VALID_PLAN)
        assert len(plan) == 3
        assert plan[0]["search_query"] == "renewable energy trends 2025"

    def test_raises_on_too_few_steps(self):
        with pytest.raises(ValueError, match="between 3 and 5"):
            validate_plan(VALID_PLAN[:2])

    def test_raises_on_empty_search_query(self):
        bad_plan = [
            *VALID_PLAN[:2],
            {"step": 3, "search_query": "", "goal": "Missing query"},
        ]
        with pytest.raises(ValueError, match="search_query"):
            validate_plan(bad_plan)


class TestResearcherExecuteStep:
    def test_runs_search_extract_and_save(self):
        async def run():
            researcher = Researcher()
            mock_session = AsyncMock()

            async def fake_call_tool(session, name, arguments):
                if name == "web_search":
                    return MOCK_SEARCH_RESULTS
                if name == "extract_content":
                    return "Full page text content."
                if name == "save_note":
                    return f"Note saved under key '{arguments['key']}'."
                raise AssertionError(f"Unexpected tool: {name}")

            with patch.object(researcher, "_call_tool", side_effect=fake_call_tool):
                return await researcher._execute_step(mock_session, VALID_PLAN[0])

        result = asyncio.run(run())

        assert result["search_results"] == MOCK_SEARCH_RESULTS
        assert len(result["extractions"]) == 1
        assert result["extractions"][0]["content"] == "Full page text content."
        assert "step-1-" in result["note_key"]

    def test_propagates_search_errors(self):
        async def run():
            researcher = Researcher()
            with patch.object(
                researcher,
                "_call_tool",
                side_effect=RuntimeError("Tavily search failed"),
            ):
                await researcher._execute_step(AsyncMock(), VALID_PLAN[0])

        with pytest.raises(RuntimeError, match="Tavily"):
            asyncio.run(run())


class TestResearcherExecutePlan:
    def test_executes_all_plan_steps(self):
        async def run():
            researcher = Researcher()
            step_result = {
                "step": 1,
                "search_query": "q",
                "goal": "g",
                "search_results": [],
                "extractions": [],
                "note_key": "step-1-q",
                "save_confirmation": "saved",
            }

            with patch.object(
                researcher,
                "_execute_step",
                new_callable=AsyncMock,
                return_value=step_result,
            ) as mock_step, patch(
                "agents.researcher.run_with_session",
                new_callable=AsyncMock,
            ) as mock_run:

                async def invoke(_params, callback):
                    return await callback(AsyncMock())

                mock_run.side_effect = invoke
                result = await researcher.execute_plan(VALID_PLAN)
                assert mock_step.call_count == 3
                return result

        result = asyncio.run(run())

        assert len(result["steps"]) == 3
        assert "context" in result
        assert result["system_prompt"]

    def test_raises_on_invalid_plan_length(self):
        async def run():
            researcher = Researcher()
            await researcher.execute_plan(VALID_PLAN[:1])

        with pytest.raises(ValueError, match="between 3 and 5"):
            asyncio.run(run())


class TestResearcherRunPlan:
    def test_wraps_execute_plan_with_asyncio_run(self):
        researcher = Researcher()
        mock_result = {"context": "done", "steps": []}

        async def fake_execute_plan(plan):
            return mock_result

        with patch.object(
            researcher, "execute_plan", side_effect=fake_execute_plan
        ), patch("agents.researcher.asyncio.run", return_value=mock_result) as mock_run:
            result = researcher.run_plan(VALID_PLAN)

        assert result == mock_result
        mock_run.assert_called_once()


class TestConductResearch:
    def test_delegates_to_researcher(self):
        mock_result = {"context": "research output", "plan": VALID_PLAN}
        mock_researcher = MagicMock()
        mock_researcher.run_plan.return_value = mock_result

        result = conduct_research(VALID_PLAN, researcher=mock_researcher)

        assert result == mock_result
        mock_researcher.run_plan.assert_called_once_with(VALID_PLAN)
