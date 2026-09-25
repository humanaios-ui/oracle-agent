"""Unit tests for oracle.run_oracle using a mocked Anthropic client."""
from __future__ import annotations

import logging

import pytest

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


def _full_steps():
    return [
        {
            "step": n,
            "witness_witch_warlock_finding": "finding",
            "jester_challenges_on_this_step": "none",
            "oracle_integration": "",
            "revised_finding": "revised",
        }
        for n in range(1, 8)
    ]


def _full_extensions():
    return [
        {"extension": letter, "jester_challenges": "none", "oracle_assessment": "assessment"}
        for letter in "ABCDE"
    ]


def _diagnosis_payload(challenge_ids, *, steps=None, extensions=None):
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
        "steps": steps if steps is not None else _full_steps(),
        "extensions": extensions if extensions is not None else _full_extensions(),
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


def test_run_oracle_rejects_missing_step(monkeypatch):
    incomplete_steps = _full_steps()[:-1]  # drop step 7
    payload = _diagnosis_payload(["J1", "J2"], steps=incomplete_steps)
    fake_client = _FakeClient(
        [_FakeMessage([_FakeBlock("tool_use", "submit_oracle_diagnosis", payload)])]
    )
    monkeypatch.setattr(claude_client, "get_client", lambda: fake_client)

    with pytest.raises(claude_client.OracleAgentError, match="Steps 1-7"):
        run_oracle("witness", "witch warlock", JESTER_OUTPUT, incident_id="IC-063")


def test_run_oracle_rejects_duplicate_extension(monkeypatch):
    duplicate_extensions = _full_extensions()[:-1] + [_full_extensions()[0]]  # A appears twice, E missing
    payload = _diagnosis_payload(["J1", "J2"], extensions=duplicate_extensions)
    fake_client = _FakeClient(
        [_FakeMessage([_FakeBlock("tool_use", "submit_oracle_diagnosis", payload)])]
    )
    monkeypatch.setattr(claude_client, "get_client", lambda: fake_client)

    with pytest.raises(claude_client.OracleAgentError, match="Extensions A-E"):
        run_oracle("witness", "witch warlock", JESTER_OUTPUT, incident_id="IC-063")


def test_run_oracle_rejects_malformed_extension_label(monkeypatch):
    # "Aardvark" starts with a valid letter but isn't one -- a naive
    # first-character check would wrongly accept it as extension A.
    malformed = _full_extensions()
    malformed[0] = {**malformed[0], "extension": "Aardvark"}
    payload = _diagnosis_payload(["J1", "J2"], extensions=malformed)
    fake_client = _FakeClient(
        [_FakeMessage([_FakeBlock("tool_use", "submit_oracle_diagnosis", payload)])]
    )
    monkeypatch.setattr(claude_client, "get_client", lambda: fake_client)

    with pytest.raises(claude_client.OracleAgentError, match="malformed extension label"):
        run_oracle("witness", "witch warlock", JESTER_OUTPUT, incident_id="IC-063")


def test_run_oracle_accepts_labeled_extension_form(monkeypatch):
    labeled = [
        {**ext, "extension": f"{ext['extension']} (Some Description)"} for ext in _full_extensions()
    ]
    payload = _diagnosis_payload(["J1", "J2"], extensions=labeled)
    fake_client = _FakeClient(
        [_FakeMessage([_FakeBlock("tool_use", "submit_oracle_diagnosis", payload)])]
    )
    monkeypatch.setattr(claude_client, "get_client", lambda: fake_client)

    result = run_oracle("witness", "witch warlock", JESTER_OUTPUT, incident_id="IC-063")
    assert len(result.extensions) == 5
