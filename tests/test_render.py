"""Smoke tests for the deterministic PR #3 markdown renderer."""
from __future__ import annotations

from datetime import datetime, timezone

from oracle_agent.models import (
    ExtensionAssessment,
    JesterChallenge,
    JesterIntegration,
    JesterOutput,
    OracleDiagnosis,
    OracleOutput,
    StepFinding,
)
from oracle_agent.render import render_pr3


def _sample_outputs():
    jester_output = JesterOutput(
        challenges=[
            JesterChallenge(
                challenge_id="J1",
                step="3",
                question="Is it absent or never designed?",
                target="Step 3",
                why_it_matters="changes remedy",
                severity="high",
                evidence_pointer=None,
            )
        ]
    )
    oracle_output = OracleOutput(
        incident_id="IC-063",
        jester_integration=[
            JesterIntegration(
                challenge_id="J1",
                validity="valid",
                impact_on_diagnosis="clarifies remedy",
                unknowns_highlighted=["design intent"],
            )
        ],
        steps=[
            StepFinding(
                step=3,
                witness_witch_warlock_finding="Boundary: ABSENT",
                jester_challenges_on_this_step="J1",
                oracle_integration="clarified",
                revised_finding="Boundary never mechanically enforced",
            )
        ],
        extensions=[
            ExtensionAssessment(
                extension="A (Epistemic Status)", jester_challenges="none", oracle_assessment="OBSERVED"
            )
        ],
        diagnosis=OracleDiagnosis(
            mechanism_diagnosis=["BOUNDARY-FAILURE", "CUSTODY-BREAKDOWN"],
            mechanism_uncertainty="",
            standing="MECHANISM_MITIGATED / ROOT_OF_TRUST_UNRESOLVED / PARTIALLY_CONTAINED",
            standing_explanation="Mechanism fixed post-incident; root of trust still open.",
            unknowns_preserved=["Z2 key provenance"],
            remedy_scope_points=10,
            remedy_outline="See Witness + Witch/Warlock analysis.",
        ),
    )
    return jester_output, oracle_output


def test_render_pr3_contains_required_sections():
    jester_output, oracle_output = _sample_outputs()
    markdown = render_pr3(
        "IC-063",
        jester_output,
        oracle_output,
        witness_pr=1,
        witch_warlock_pr=2,
        generated_at=datetime(2026, 9, 24, tzinfo=timezone.utc),
    )

    assert "# IC-063 Lawson Diagnostic Audit" in markdown
    assert "Witness PR #1, Witch/Warlock PR #2" in markdown
    assert "J1" in markdown
    assert "MECHANISM_MITIGATED / ROOT_OF_TRUST_UNRESOLVED / PARTIALLY_CONTAINED" in markdown
    assert "Z2 Decision Required" in markdown
    assert "Remedy Scope:** 10 points" in markdown
