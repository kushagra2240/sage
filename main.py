"""CLI entry point for the Sage multi-agent research assistant."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Callable, TextIO

from agents.analyst import analyze_findings
from agents.orchestrator import Orchestrator
from agents.writer import write_report
from config import ConfigError, validate_config

LogFn = Callable[[str], None]


def _default_log(message: str, stream: TextIO | None = None) -> None:
    print(message, file=stream or sys.stderr)


def run_pipeline(
    orchestrator: Orchestrator,
    query: str,
    audience: str = "general",
    log: LogFn | None = None,
) -> dict[str, Any]:
    """
    Run the full research pipeline with progress logging at each stage.

    Stages: plan → research (MCP) → analyze → write.
    """
    emit = log or _default_log
    question = query.strip()

    emit("[1/4] Planning research strategy with Claude...")
    plan = orchestrator.create_plan(question)
    emit(f"      Created {len(plan)}-step plan.")
    for step in plan:
        emit(f"      • Step {step['step']}: {step['search_query']}")

    emit("[2/4] Gathering information via MCP tools (search, extract, notes)...")
    research = orchestrator.researcher.run_plan(plan)
    step_count = len(research.get("steps", []))
    emit(f"      Completed {step_count} research steps.")

    emit("[3/4] Analyzing findings across sources...")
    analysis_result = analyze_findings(research["context"])
    emit(
        f"      Analysis complete "
        f"({analysis_result['usage']['output_tokens']} output tokens)."
    )

    emit("[4/4] Writing final report...")
    report_result = write_report(
        analysis_result["analysis"],
        audience=audience,
    )
    emit(
        f"      Report complete "
        f"({report_result['usage']['output_tokens']} output tokens)."
    )

    return {
        "query": question,
        "model": orchestrator.model,
        "plan": plan,
        "research": research,
        "analysis": analysis_result,
        "report": report_result,
    }


def save_report(report_text: str, output_path: Path) -> None:
    """Write the final report to disk, creating parent directories if needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sage — multi-agent research assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            '  python main.py --query "How does RAG work?" --output report.md'
        ),
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Research topic or question to investigate",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Path to save the final markdown report",
    )
    parser.add_argument(
        "--audience",
        default="general",
        help="Target audience for the final report (default: general)",
    )
    args = parser.parse_args(argv)

    if not args.query.strip():
        print("Error: --query must not be empty.", file=sys.stderr)
        return 1

    try:
        validate_config()
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        print("Copy .env.example to .env and set your API keys.", file=sys.stderr)
        return 1

    orchestrator = Orchestrator()
    print(f"Starting Sage research pipeline for: {args.query.strip()!r}\n", file=sys.stderr)

    try:
        result = run_pipeline(
            orchestrator,
            args.query,
            audience=args.audience,
        )
    except ValueError as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Pipeline error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1

    report_text = result["report"]["report"]

    if args.output:
        try:
            save_report(report_text, args.output)
        except OSError as exc:
            print(f"Failed to write report: {exc}", file=sys.stderr)
            return 1
        print(f"\nReport saved to {args.output.resolve()}", file=sys.stderr)
    else:
        print(report_text)

    print("\nDone.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
