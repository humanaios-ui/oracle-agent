"""Unit tests for oracle.run_oracle using a mocked Anthropic client."""
from __future__ import annotations

import logging

from oracle_agent import claude_client
from oracle_agent.models import JesterChallenge, JesterOutput
from oracle_agent.oracle import run_oracle

from .test_jester import _FakeBlock, _FakeClient, _FakeMessage

JESTER_OUTPUT = JesterOutput(
    challenges=[
        JesterChallenge(
            challenge_id="J1",
            step="3",
            question="q1",
            target="t1",
            why_it_matters="w1",
            severity="high",
            evidence_pointer=None,
        ),
        JesterChallenge(
            challenge_id="J2",
            step="4",
            question="q2",
            target="t2",
            why_it_matters="w2",
            severity="medium",
            evidence_pointer=None,
        ),
    ]
)


def _diagnosis_payload(challenge_ids):
    return {
        "incident_id": "IC-WRONG",  # deliberately wrong, to test the override
        "jester_integration": [
            {
                "challenge_id": cid,
                "validity": "valid",
                "impact_on_diagnosis": "refines finding",
                "unknowns_highlighted": [],
            }
            for cid in challenge_ids
        ],
        "steps": [
            {
                "step": 1,
                "witness_witch_warlock_finding": "finding",
                "jester_challenges_on_this_step": "none",
                "oracle_integration": "",
                "revised_finding": "revised",
            }
        ],
        "extensions": [
            {"extension": "A", "jester_challenges": "none", "oracle_assessment": "assessment"}
        ],
        "diagnosis": {
            "mechanism_diagnosis": ["BOUNDARY-FAILURE"],
            "mechanism_uncertainty": "",
            "standing": "MECHANISM_MITIGATED / ROOT_OF_TRUST_UNRESOLVED / PARTIALLY_CONTAINED",
            "standing_explanation": "explanation",
            "unknowns_preserved": ["unknown 1"],
            "remedy_scope_points": 3,
            "remedy_outline": "outline",
        },
    }


def test_run_oracle_parses_and_overrides_incident_id(monkeypatch):
    payload = _diagnosis_payload(["J1", "J2"])
    fake_client = _FakeClient(
        [_FakeMessage([_FakeBlock("tool_use", "submit_oracle_diagnosis", payload)])]
    )
    monkeypatch.setattr(claude_client, "get_client", lambda: fake_client)

    result = run_oracle("witness", "witch warlock", JESTER_OUTPUT, incident_id="IC-063")

    assert result.incident_id == "IC-063"  # caller's incident_id wins, not the model's echo
    assert len(result.jester_integration) == 2
    assert result.missing_challenge_ids(JESTER_OUTPUT) == []


def test_run_oracle_logs_when_challenge_dropped(monkeypatch, caplog):
    payload = _diagnosis_payload(["J1"])  # J2 missing -> Rule 1 violation
    fake_client = _FakeClient(
        [_FakeMessage([_FakeBlock("tool_use", "submit_oracle_diagnosis", payload)])]
    )
    monkeypatch.setattr(claude_client, "get_client", lambda: fake_client)

    with caplog.at_level(logging.WARNING):
        result = run_oracle("witness", "witch warlock", JESTER_OUTPUT, incident_id="IC-063")

    assert result.missing_challenge_ids(JESTER_OUTPUT) == ["J2"]
    assert any("Rule 1 violation" in record.message for record in caplog.records)
