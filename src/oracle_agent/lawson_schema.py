"""Reference constants for the Lawson Diagnostic Audit's 10-step / 5-extension
schema. See docs/ORACLE_SYNTHESIS_RULES.md and docs/JESTER_PROMPT_DESIGN.md
(OI-ORACLE-01) for the full design.
"""

STEPS = {
    1: "Consequence",
    2: "Authority State",
    3: "Boundary State",
    4: "Custody",
    5: "Actor Behavior",
    6: "Capability Acquisition",
    7: "Mechanism",
}

EXTENSIONS = {
    "A": "Epistemic Status",
    "B": "Temporal State",
    "C": "Evidence Independence",
    "D": "Reversibility & Exposure",
    "E": "Counterfactual Control",
}

MECHANISM_STATUS = ["ABSENT", "PRESENT", "MITIGATED", "PARTIALLY_MITIGATED", "UNKNOWN"]
ROOT_OF_TRUST_STATUS = ["ESTABLISHED", "UNRESOLVED", "PARTIALLY_UNRESOLVED", "UNKNOWN"]
EXPOSURE_STATUS = ["CONTAINED", "PARTIALLY_CONTAINED", "ONGOING", "REVERSED", "UNKNOWN"]
