"""CLI entry point for the Sage multi-agent research assistant."""

from __future__ import annotations

import argparse
import builtins
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, TextIO

from agents.analyst import analyze_findings
from agents.orchestrator import Orchestrator
from agents.writer import write_report
from config import ConfigError, validate_config

LogFn = Callable[[str], None]


def _default_log(message: str, stream: TextIO | None = None) -> None:
    print(message, file=stream or sys.stderr)


# BaseExceptionGroup is a builtin only on Python 3.11+; resolve it safely
# so this module keeps working on Python 3.10.
_EXCEPTION_GROUP = getattr(builtins, "BaseExceptionGroup", None)


def _format_exception(exc: BaseException) -> str:
    """Format an exception, unwrapping ExceptionGroup on Python 3.11+."""
    parts = [str(exc)]
    if _EXCEPTION_GROUP is not None and isinstance(exc, _EXCEPTION_GROUP):
        for i, sub in enumerate(exc.exceptions):
            parts.append(f"  [{i + 1}] {type(sub).__name__}: {sub}")
    return "\n".join(parts)


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
    provider_label = orchestrator.provider_name

    emit(f"[1/4] Planning research strategy ({provider_label})...")
    plan = orchestrator.create_plan(question)
    emit(f"      Created {len(plan)}-step plan.")
    for step in plan:
        emit(f"      • Step {step['step']}: {step['search_query']}")

    emit("[2/4] Gathering information via MCP tools (search, extract, notes)...")
    research = orchestrator.researcher.run_plan(plan)
    step_count = len(research.get("steps", []))
    emit(f"      Completed {step_count} research steps.")

    emit(f"[3/4] Analyzing findings ({orchestrator.model})...")
    analysis_result = analyze_findings(
        research["context"],
        model=orchestrator.model,
        provider=orchestrator.provider,
    )
    emit(
        f"      Analysis complete "
        f"({analysis_result['usage']['output_tokens']} output tokens)."
    )

    emit(f"[4/4] Writing final report ({orchestrator.model})...")
    report_result = write_report(
        analysis_result["analysis"],
        audience=audience,
        model=orchestrator.model,
        provider=orchestrator.provider,
    )
    emit(
        f"      Report complete "
        f"({report_result['usage']['output_tokens']} output tokens)."
    )

    return {
        "query": question,
        "provider": orchestrator.provider_name,
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
            "Examples:\n"
            '  python main.py --query "How does RAG work?" --output report.md\n'
            "  python main.py --query \"Topic\" --provider openai --model llama3.3"
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
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai"],
        help="LLM provider (default: LLM_PROVIDER from .env or anthropic)",
    )
    parser.add_argument(
        "--model",
        help="Model id override (default: ANTHROPIC_MODEL or OPENAI_MODEL from .env)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print full traceback on failure",
    )
    args = parser.parse_args(argv)

    if not args.query.strip():
        print("Error: --query must not be empty.", file=sys.stderr)
        return 1

    try:
        config = validate_config(provider=args.provider)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        print("Copy .env.example to .env and set your API keys.", file=sys.stderr)
        return 1

    provider_name = config["llm_provider"]
    model = args.model or config["model"]
    orchestrator = Orchestrator(provider=provider_name, model=model)

    print(
        f"Starting Sage ({provider_name}, {model}) for: {args.query.strip()!r}\n",
        file=sys.stderr,
    )

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
        if args.verbose:
            traceback.print_exc()
        return 1
    except Exception as exc:
        print(f"Pipeline failed:\n{_format_exception(exc)}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
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
