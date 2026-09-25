"""Unit tests for JesterOutput's challenge_id validation."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from oracle_agent.models import JesterChallenge, JesterOutput


def _challenge(challenge_id: str) -> JesterChallenge:
    return JesterChallenge(
        challenge_id=challenge_id,
        step="1",
        question="q",
        target="t",
        why_it_matters="w",
        severity="low",
        evidence_pointer=None,
    )


def test_jester_output_accepts_unique_ids():
    output = JesterOutput(challenges=[_challenge("J1"), _challenge("J2")])
    assert [c.challenge_id for c in output.challenges] == ["J1", "J2"]


def test_jester_output_rejects_duplicate_ids():
    with pytest.raises(ValidationError, match="duplicates"):
        JesterOutput(challenges=[_challenge("J1"), _challenge("J1")])


def test_jester_output_rejects_blank_id():
    with pytest.raises(ValidationError, match="non-empty"):
        JesterOutput(challenges=[_challenge("J1"), _challenge("   ")])
