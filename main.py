"""CLI entry point for the Sage multi-agent research assistant."""

import argparse
import json
import sys

from config import ConfigError, validate_config
from agents.orchestrator import run_research_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sage — multi-agent research assistant"
    )
    parser.add_argument(
        "query",
        help="Research topic or question to investigate",
    )
    parser.add_argument(
        "--audience",
        default="general",
        help="Target audience for the final report (default: general)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Maximum Tavily search results (default: 5)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full pipeline output as JSON",
    )
    args = parser.parse_args(argv)

    try:
        validate_config()
        result = run_research_pipeline(
            args.query,
            audience=args.audience,
            max_results=args.max_results,
        )
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["report"]["report"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
