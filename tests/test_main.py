"""Tests for main CLI."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from main import main, run_pipeline, save_report

MOCK_PIPELINE_RESULT = {
    "query": "test topic",
    "provider": "anthropic",
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


def _mock_orchestrator():
    orch = MagicMock()
    orch.provider_name = "anthropic"
    orch.model = "claude-sonnet-4-6"
    orch.provider = MagicMock()
    orch.create_plan.return_value = MOCK_PIPELINE_RESULT["plan"]
    orch.researcher.run_plan.return_value = MOCK_PIPELINE_RESULT["research"]
    return orch


class TestRunPipeline:
    @patch("main.write_report")
    @patch("main.analyze_findings")
    def test_runs_all_stages(self, mock_analyze, mock_write):
        mock_orchestrator = _mock_orchestrator()
        mock_analyze.return_value = MOCK_PIPELINE_RESULT["analysis"]
        mock_write.return_value = MOCK_PIPELINE_RESULT["report"]

        logs: list[str] = []
        result = run_pipeline(mock_orchestrator, "test topic", log=logs.append)

        assert result["report"]["report"] == "Final report body."
        assert any("[1/4]" in line for line in logs)
        assert any("anthropic" in line for line in logs)


class TestSaveReport:
    def test_writes_report_to_file(self, tmp_path: Path):
        output = tmp_path / "reports" / "out.md"
        save_report("# Report\n\nContent here.", output)
        assert output.read_text(encoding="utf-8") == "# Report\n\nContent here."


class TestMain:
    @patch("main.run_pipeline")
    @patch("main.Orchestrator")
    @patch("main.validate_config")
    def test_prints_report_when_no_output(
        self, mock_validate, mock_orch_cls, mock_pipeline, capsys
    ):
        mock_validate.return_value = {
            "llm_provider": "anthropic",
            "model": "claude-sonnet-4-6",
        }
        mock_orch_cls.return_value = _mock_orchestrator()
        mock_pipeline.return_value = MOCK_PIPELINE_RESULT

        code = main(["--query", "test topic"])
        captured = capsys.readouterr()
        assert code == 0
        assert "Final report body." in captured.out

    @patch("main.run_pipeline")
    @patch("main.Orchestrator")
    @patch("main.validate_config")
    def test_saves_report_to_output_path(
        self, mock_validate, mock_orch_cls, mock_pipeline, tmp_path: Path, capsys
    ):
        mock_validate.return_value = {
            "llm_provider": "anthropic",
            "model": "claude-sonnet-4-6",
        }
        mock_orch_cls.return_value = _mock_orchestrator()
        mock_pipeline.return_value = MOCK_PIPELINE_RESULT

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
    @patch("main.Orchestrator")
    @patch("main.validate_config")
    def test_handles_pipeline_runtime_error(
        self, mock_validate, mock_orch_cls, mock_pipeline, capsys
    ):
        mock_validate.return_value = {
            "llm_provider": "anthropic",
            "model": "claude-sonnet-4-6",
        }
        mock_orch_cls.return_value = _mock_orchestrator()
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
