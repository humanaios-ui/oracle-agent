"""Pydantic schemas for Jester challenges and Oracle diagnoses.

Mirrors the JSON structures defined in oracle-agent-service-spec.md and
oracle-synthesis-rules.md (OI-ORACLE-01).
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high"]
Validity = Literal["valid", "partial", "questionable", "speculative"]


class JesterChallenge(BaseModel):
    challenge_id: str
    step: str
    question: str
    target: str
    why_it_matters: str
    severity: Severity
    evidence_pointer: Optional[str] = None


class JesterOutput(BaseModel):
    challenges: list[JesterChallenge] = Field(default_factory=list)
    output_tokens: int = 0
    model: str = ""


class JesterIntegration(BaseModel):
    challenge_id: str
    validity: Validity
    impact_on_diagnosis: str
    unknowns_highlighted: list[str] = Field(default_factory=list)


class StepFinding(BaseModel):
    step: int
    witness_witch_warlock_finding: str
    jester_challenges_on_this_step: str = "none"
    oracle_integration: str = ""
    revised_finding: str


class ExtensionAssessment(BaseModel):
    extension: str
    jester_challenges: str = "none"
    oracle_assessment: str


class OracleDiagnosis(BaseModel):
    mechanism_diagnosis: list[str]
    mechanism_uncertainty: str = ""
    standing: str
    standing_explanation: str
    unknowns_preserved: list[str] = Field(default_factory=list)
    remedy_scope_points: int
    remedy_outline: str


class OracleOutput(BaseModel):
    incident_id: str
    jester_integration: list[JesterIntegration]
    steps: list[StepFinding]
    extensions: list[ExtensionAssessment]
    diagnosis: OracleDiagnosis
    output_tokens: int = 0
    model: str = ""

    def missing_challenge_ids(self, jester_output: JesterOutput) -> list[str]:
        """Rule 1 check (ORACLE_SYNTHESIS_RULES.md): every Jester challenge
        must appear in the diagnosis. Returns challenge_ids Oracle dropped.
        """
        integrated = {i.challenge_id for i in self.jester_integration}
        return [c.challenge_id for c in jester_output.challenges if c.challenge_id not in integrated]
