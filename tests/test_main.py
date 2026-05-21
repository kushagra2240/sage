"""Tests for main CLI."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from main import main, run_pipeline, save_report


MOCK_PIPELINE_RESULT = {
    "query": "test topic",
    "model": "claude-sonnet-4-6",
    "plan": [{"step": 1, "search_query": "q1", "goal": "g1"}] * 3,
    "research": {"context": "research context", "steps": [{}, {}, {}]},
    "analysis": {
        "analysis": "analysis text",
        "usage": {"input_tokens": 10, "output_tokens": 20},
    },
    "report": {
        "report": "Final report body.",
        "usage": {"input_tokens": 30, "output_tokens": 100},
    },
}


class TestRunPipeline:
    @patch("main.write_report")
    @patch("main.analyze_findings")
    def test_runs_all_stages(self, mock_analyze, mock_write):
        mock_orchestrator = MagicMock()
        mock_orchestrator.model = "claude-sonnet-4-6"
        mock_orchestrator.create_plan.return_value = MOCK_PIPELINE_RESULT["plan"]
        mock_orchestrator.researcher.run_plan.return_value = MOCK_PIPELINE_RESULT[
            "research"
        ]
        mock_analyze.return_value = MOCK_PIPELINE_RESULT["analysis"]
        mock_write.return_value = MOCK_PIPELINE_RESULT["report"]

        logs: list[str] = []
        result = run_pipeline(
            mock_orchestrator, "test topic", log=logs.append
        )

        assert result["report"]["report"] == "Final report body."
        assert any("[1/4]" in line for line in logs)
        assert any("[4/4]" in line for line in logs)
        mock_orchestrator.create_plan.assert_called_once()
        mock_orchestrator.researcher.run_plan.assert_called_once()

    @patch("main.write_report")
    @patch("main.analyze_findings")
    def test_propagates_planning_errors(self, mock_analyze, mock_write):
        mock_orchestrator = MagicMock()
        mock_orchestrator.create_plan.side_effect = RuntimeError("API rate limit")

        with pytest.raises(RuntimeError, match="rate limit"):
            run_pipeline(mock_orchestrator, "test topic", log=lambda _: None)


class TestSaveReport:
    def test_writes_report_to_file(self, tmp_path: Path):
        output = tmp_path / "reports" / "out.md"
        save_report("# Report\n\nContent here.", output)
        assert output.read_text(encoding="utf-8") == "# Report\n\nContent here."


class TestMain:
    @patch("main.run_pipeline", return_value=MOCK_PIPELINE_RESULT)
    @patch("main.validate_config")
    def test_prints_report_when_no_output(self, _mock_validate, _mock_pipeline, capsys):
        code = main(["--query", "test topic"])
        captured = capsys.readouterr()
        assert code == 0
        assert "Final report body." in captured.out
        assert "Done." in captured.err

    @patch("main.run_pipeline", return_value=MOCK_PIPELINE_RESULT)
    @patch("main.validate_config")
    def test_saves_report_to_output_path(
        self, _mock_validate, _mock_pipeline, tmp_path: Path, capsys
    ):
        output = tmp_path / "report.md"
        code = main(["--query", "test topic", "--output", str(output)])
        captured = capsys.readouterr()

        assert code == 0
        assert output.read_text(encoding="utf-8") == "Final report body."
        assert "Report saved" in captured.err

    @patch("main.validate_config")
    def test_returns_error_on_config_failure(self, mock_validate, capsys):
        from config import ConfigError

        mock_validate.side_effect = ConfigError("ANTHROPIC_API_KEY is not set")
        code = main(["--query", "test topic"])
        captured = capsys.readouterr()
        assert code == 1
        assert "Configuration error" in captured.err

    @patch("main.run_pipeline")
    @patch("main.validate_config")
    def test_handles_pipeline_runtime_error(self, _mock_validate, mock_pipeline, capsys):
        mock_pipeline.side_effect = RuntimeError("Tavily search failed")
        code = main(["--query", "test topic"])
        captured = capsys.readouterr()
        assert code == 1
        assert "Pipeline error" in captured.err

    def test_rejects_empty_query(self, capsys):
        code = main(["--query", "   "])
        captured = capsys.readouterr()
        assert code == 1
        assert "empty" in captured.err.lower()
