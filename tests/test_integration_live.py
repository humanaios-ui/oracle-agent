"""Optional end-to-end test against the real Anthropic API.

Skipped unless ANTHROPIC_API_KEY is set -- not part of the default CI run
(.github/workflows/test.yml runs the mocked unit tests only). Run manually:

    ANTHROPIC_API_KEY=... pytest tests/test_integration_live.py
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from oracle_agent.jester import run_jester
from oracle_agent.oracle import run_oracle
from oracle_agent.render import render_pr3

FIXTURES = Path(__file__).parent / "fixtures"

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires a real ANTHROPIC_API_KEY; not run in CI",
)


def test_ic063_end_to_end():
    witness = (FIXTURES / "witness.md").read_text()
    witch_warlock = (FIXTURES / "witch_warlock.md").read_text()

    jester_output = run_jester(witness, witch_warlock)
    assert 1 <= len(jester_output.challenges) <= 5

    oracle_output = run_oracle(witness, witch_warlock, jester_output, incident_id="IC-063")
    assert oracle_output.missing_challenge_ids(jester_output) == []

    markdown = render_pr3("IC-063", jester_output, oracle_output)
    assert "Z2 Decision Required" in markdown
