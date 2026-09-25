"""Oracle: synthesizes Witness + Witch/Warlock + Jester into one diagnosis.

See docs/ORACLE_SYNTHESIS_RULES.md for the full non-negotiable rule set.
Oracle never makes the Z2 remedy decision, never closes a Jester-raised
unknown, and never recommends a specific fix.
"""
from __future__ import annotations

import logging
from typing import Optional

from .claude_client import call_structured
from .models import JesterOutput, OracleOutput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Oracle in a Lawson Diagnostic Audit.

Your role: Synthesize Witness + Witch/Warlock + Jester inputs into a single diagnosis.

CONSTRAINTS:
- You do NOT make Z2 remedy decisions (say "Z2 must decide")
- You do NOT close unknowns Jester raised
- You do NOT contradict Witness/Witch/Warlock without strong evidence
- You do NOT recommend specific fixes (that's Z2's job)
- You acknowledge every Jester challenge in your diagnosis

RULES (HARD LIMITS):
1. Every Jester challenge appears in your jester_integration list, by its challenge_id
2. Unknowns raised by Jester are preserved (not inferred away)
3. Contradictions are noted, not hidden
4. Confidence can downgrade (e.g. OBSERVED -> INFERRED), never upgrade
   (e.g. INFERRED -> OBSERVED) based on Jester reasoning alone
5. Remedy scope is your job (how many distinct fixes, what they are);
   the decision of which to implement and when is Z2's
6. Jester challenges refine existing findings; only add a new remedy point
   if a challenge reveals a genuinely separate mechanism

For each Jester challenge: decide if it is valid, say how it changes (or doesn't
change) the diagnosis, and list any unknowns it highlights.

Then synthesize:
- Steps 1-7 (witness/witch/warlock finding + jester integration + revised finding)
- Extensions A-E (epistemic status, temporal state, evidence independence,
  reversibility, counterfactual control)
- Mechanism (non-exclusive list of failure categories), standing
  ("MECHANISM_[status] / ROOT_OF_TRUST_[status] / EXPOSURE_[status]"),
  unknowns preserved, and remedy scope

Call the submit_oracle_diagnosis tool with your answer. Do not respond in plain text."""

DIAGNOSIS_TOOL = {
    "name": "submit_oracle_diagnosis",
    "description": "Submit the Oracle's full synthesized diagnosis.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "incident_id": {"type": "string"},
            "jester_integration": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "challenge_id": {"type": "string"},
                        "validity": {
                            "type": "string",
                            "enum": ["valid", "partial", "questionable", "speculative"],
                        },
                        "impact_on_diagnosis": {"type": "string"},
                        "unknowns_highlighted": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "challenge_id",
                        "validity",
                        "impact_on_diagnosis",
                        "unknowns_highlighted",
                    ],
                    "additionalProperties": False,
                },
            },
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "step": {"type": "integer"},
                        "witness_witch_warlock_finding": {"type": "string"},
                        "jester_challenges_on_this_step": {"type": "string"},
                        "oracle_integration": {"type": "string"},
                        "revised_finding": {"type": "string"},
                    },
                    "required": [
                        "step",
                        "witness_witch_warlock_finding",
                        "jester_challenges_on_this_step",
                        "oracle_integration",
                        "revised_finding",
                    ],
                    "additionalProperties": False,
                },
            },
            "extensions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "extension": {"type": "string"},
                        "jester_challenges": {"type": "string"},
                        "oracle_assessment": {"type": "string"},
                    },
                    "required": ["extension", "jester_challenges", "oracle_assessment"],
                    "additionalProperties": False,
                },
            },
            "diagnosis": {
                "type": "object",
                "properties": {
                    "mechanism_diagnosis": {"type": "array", "items": {"type": "string"}},
                    "mechanism_uncertainty": {"type": "string"},
                    "standing": {"type": "string"},
                    "standing_explanation": {"type": "string"},
                    "unknowns_preserved": {"type": "array", "items": {"type": "string"}},
                    "remedy_scope_points": {"type": "integer"},
                    "remedy_outline": {"type": "string"},
                },
                "required": [
                    "mechanism_diagnosis",
                    "mechanism_uncertainty",
                    "standing",
                    "standing_explanation",
                    "unknowns_preserved",
                    "remedy_scope_points",
                    "remedy_outline",
                ],
                "additionalProperties": False,
            },
        },
        "required": ["incident_id", "jester_integration", "steps", "extensions", "diagnosis"],
        "additionalProperties": False,
    },
}


def run_oracle(
    witness_markdown: str,
    witch_warlock_markdown: str,
    jester_output: JesterOutput,
    *,
    incident_id: str,
    model: Optional[str] = None,
) -> OracleOutput:
    jester_json = [c.model_dump() for c in jester_output.challenges]
    user_prompt = (
        f"INCIDENT: {incident_id}\n\n"
        f"WITNESS (Steps 1-3, Extensions A-D):\n{witness_markdown}\n\n"
        f"WITCH/WARLOCK (Steps 4, 7):\n{witch_warlock_markdown}\n\n"
        f"JESTER CHALLENGES:\n{jester_json}\n\n"
        "Synthesize the full Oracle diagnosis."
    )
    result = call_structured(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        tool=DIAGNOSIS_TOOL,
        model=model,
    )

    # incident_id is authoritative from our own call site, never from the
    # model's own (possibly mistranscribed) echo of it.
    data = dict(result.data)
    data["incident_id"] = incident_id
    output = OracleOutput(**data, output_tokens=result.output_tokens, model=result.model)

    missing = output.missing_challenge_ids(jester_output)
    if missing:
        logger.warning(
            "Oracle diagnosis for %s dropped Jester challenges %s (Rule 1 violation)",
            incident_id,
            missing,
        )

    return output
