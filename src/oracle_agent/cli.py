"""Command-line entry point for running an Oracle Agent audit outside the
FastMCP server -- this is what the GitHub Action (oracle-audit.yml) calls.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .jester import run_jester
from .oracle import run_oracle
from .render import render_pr3


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run a Lawson Diagnostic Audit (Jester + Oracle).")
    parser.add_argument("--witness", required=True, type=Path)
    parser.add_argument("--witch-warlock", required=True, type=Path)
    parser.add_argument("--incident-id", required=True)
    parser.add_argument("--out", required=True, type=Path, help="Path to write the PR #3 markdown")
    parser.add_argument("--witness-pr", type=int, default=None)
    parser.add_argument("--witch-warlock-pr", type=int, default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path to write raw JSON output for M1-M5 measurement",
    )
    args = parser.parse_args(argv)

    witness_markdown = args.witness.read_text()
    witch_warlock_markdown = args.witch_warlock.read_text()

    jester_output = run_jester(witness_markdown, witch_warlock_markdown, model=args.model)
    oracle_output = run_oracle(
        witness_markdown,
        witch_warlock_markdown,
        jester_output,
        incident_id=args.incident_id,
        model=args.model,
    )
    markdown = render_pr3(
        args.incident_id,
        jester_output,
        oracle_output,
        witness_pr=args.witness_pr,
        witch_warlock_pr=args.witch_warlock_pr,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(markdown)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(
                {
                    "jester_challenges": [c.model_dump() for c in jester_output.challenges],
                    "oracle_diagnosis": oracle_output.model_dump(),
                },
                indent=2,
            )
        )

    print(f"Wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
