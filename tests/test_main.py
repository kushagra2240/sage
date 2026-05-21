"""Tests for main CLI."""

from unittest.mock import patch

from main import main


MOCK_PIPELINE_RESULT = {
    "query": "test topic",
    "orchestrator_prompt": "orchestrator",
    "research": {},
    "analysis": {"analysis": "analysis text"},
    "report": {"report": "Final report body."},
}


class TestMain:
    @patch("main.run_research_pipeline", return_value=MOCK_PIPELINE_RESULT)
    @patch("main.validate_config")
    def test_prints_report_on_success(self, _mock_validate, _mock_pipeline, capsys):
        code = main(["test topic"])
        captured = capsys.readouterr()
        assert code == 0
        assert "Final report body." in captured.out

    @patch("main.validate_config")
    def test_returns_error_on_config_failure(self, mock_validate, capsys):
        from config import ConfigError

        mock_validate.side_effect = ConfigError("ANTHROPIC_API_KEY is not set")
        code = main(["test topic"])
        captured = capsys.readouterr()
        assert code == 1
        assert "Configuration error" in captured.err

    @patch("main.run_research_pipeline")
    @patch("main.validate_config")
    def test_json_output_flag(self, _mock_validate, mock_pipeline, capsys):
        mock_pipeline.return_value = MOCK_PIPELINE_RESULT
        code = main(["test topic", "--json"])
        captured = capsys.readouterr()
        assert code == 0
        assert '"report"' in captured.out
