"""Oracle: synthesizes Witness + Witch/Warlock + Jester into one diagnosis.

See docs/ORACLE_SYNTHESIS_RULES.md for the full non-negotiable rule set.
Oracle never makes the Z2 remedy decision, never closes a Jester-raised
unknown, and never recommends a specific fix.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from .claude_client import OracleAgentError, call_structured
from .models import JesterOutput, OracleOutput

logger = logging.getLogger(__name__)

REQUIRED_STEPS = frozenset(range(1, 8))
REQUIRED_EXTENSIONS = frozenset("ABCDE")

# Matches the documented "A" or "A (Epistemic Status)" extension label forms
# exactly -- unlike a bare first-character check, "Aardvark" or "A-typo"
# don't match and are treated as malformed rather than as extension A.
_EXTENSION_LABEL_RE = re.compile(r"^([A-E])(\s*\(.+\))?$")


def _extension_letter(label: str) -> Optional[str]:
    match = _EXTENSION_LABEL_RE.match(label.strip())
    return match.group(1) if match else None

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
                "minItems": 7,
                "maxItems": 7,
                "items": {
                    "type": "object",
                    "properties": {
                        "step": {"type": "integer", "enum": [1, 2, 3, 4, 5, 6, 7]},
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
                "minItems": 5,
                "maxItems": 5,
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


def _validate_shape(output: OracleOutput) -> None:
    """Enforce the Steps 1-7 / Extensions A-E cardinality the Oracle contract
    requires. The strict tool schema fixes array length and (for steps) valid
    individual values, but not uniqueness or which extension letters showed
    up -- a response with seven step-1 objects, or five extensions all
    labeled "A", still passes the schema. Catch that here rather than
    silently rendering a PR that claims the full sections are present.
    """
    step_numbers = [s.step for s in output.steps]
    seen_steps = set(step_numbers)
    duplicate_steps = {n for n in step_numbers if step_numbers.count(n) > 1}
    missing_steps = REQUIRED_STEPS - seen_steps
    if missing_steps or duplicate_steps:
        raise OracleAgentError(
            "Oracle diagnosis has an invalid Steps 1-7 set "
            f"(missing={sorted(missing_steps)}, duplicate={sorted(duplicate_steps)})"
        )

    extension_letters = [_extension_letter(e.extension) for e in output.extensions]
    malformed = [e.extension for e, letter in zip(output.extensions, extension_letters) if letter is None]
    if malformed:
        raise OracleAgentError(f"Oracle diagnosis has malformed extension label(s): {malformed}")

    # extension_letters are all guaranteed in A-E here (malformed labels were
    # rejected above), so only missing/duplicate need checking.
    seen_extensions = set(extension_letters)
    duplicate_extensions = {e for e in extension_letters if extension_letters.count(e) > 1}
    missing_extensions = REQUIRED_EXTENSIONS - seen_extensions
    if missing_extensions or duplicate_extensions:
        raise OracleAgentError(
            "Oracle diagnosis has an invalid Extensions A-E set "
            f"(missing={sorted(missing_extensions)}, duplicate={sorted(duplicate_extensions)})"
        )


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
    _validate_shape(output)

    missing = output.missing_challenge_ids(jester_output)
    if missing:
        logger.warning(
            "Oracle diagnosis for %s dropped Jester challenges %s (Rule 1 violation)",
            incident_id,
            missing,
        )

    return output
