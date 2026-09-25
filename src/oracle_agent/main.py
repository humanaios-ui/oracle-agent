"""FastMCP server exposing the Oracle Agent as an MCP tool.

For CI usage (GitHub Actions), see cli.py instead -- invoking an MCP server
from a workflow step is unnecessary ceremony; the CLI is what
oracle-audit.yml actually calls.
"""
from __future__ import annotations

from fastmcp import FastMCP

from .jester import run_jester
from .oracle import run_oracle
from .render import render_pr3

mcp = FastMCP("oracle-agent")


@mcp.tool()
def run_lawson_oracle_audit(
    witness_markdown: str,
    witch_warlock_markdown: str,
    incident_id: str,
) -> dict:
    """Run the Jester + Oracle phases of a Lawson Diagnostic Audit.

    Returns the Jester challenges, the full Oracle diagnosis, and PR-ready
    markdown for the audit's PR #3. Does not decide a remedy -- that
    remains a Z2 decision.
    """
    jester_output = run_jester(witness_markdown, witch_warlock_markdown)
    oracle_output = run_oracle(
        witness_markdown, witch_warlock_markdown, jester_output, incident_id=incident_id
    )
    markdown = render_pr3(incident_id, jester_output, oracle_output)
    return {
        "status": "success",
        "jester_challenges": [c.model_dump() for c in jester_output.challenges],
        "oracle_diagnosis": oracle_output.model_dump(),
        "pr_3_markdown": markdown,
    }


if __name__ == "__main__":
    mcp.run()
