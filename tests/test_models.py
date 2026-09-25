"""Unit tests for JesterOutput's challenge_id validation and OracleDiagnosis."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from oracle_agent.models import JesterChallenge, JesterOutput, OracleDiagnosis


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


def _diagnosis_kwargs(**overrides):
    kwargs = dict(
        mechanism_diagnosis=["BOUNDARY-FAILURE"],
        mechanism_uncertainty="",
        standing="MECHANISM_MITIGATED / ROOT_OF_TRUST_UNRESOLVED / PARTIALLY_CONTAINED",
        standing_explanation="explanation",
        unknowns_preserved=[],
        remedy_scope_points=3,
        remedy_outline="outline",
    )
    kwargs.update(overrides)
    return kwargs


def test_oracle_diagnosis_accepts_zero_remedy_scope():
    diagnosis = OracleDiagnosis(**_diagnosis_kwargs(remedy_scope_points=0))
    assert diagnosis.remedy_scope_points == 0


def test_oracle_diagnosis_rejects_negative_remedy_scope():
    with pytest.raises(ValidationError):
        OracleDiagnosis(**_diagnosis_kwargs(remedy_scope_points=-1))
