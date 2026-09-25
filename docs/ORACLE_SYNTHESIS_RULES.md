# Oracle Synthesis Rules

**Version:** 0.1
**Audience:** Z1 (implementation); Z2 (review); Claude (execution)
**Purpose:** Define how Oracle integrates Jester challenges into a single diagnosis

---

## Overview

Oracle receives three inputs:
1. **Witness findings** (Steps 1–3, Extensions A–D)
2. **Witch/Warlock findings** (Steps 4, 7, mechanisms)
3. **Jester challenges** (3–5 adversarial questions)

Oracle's job: **Synthesize all three into a single diagnosis that acknowledges and addresses every Jester challenge.**

Oracle's constraints:
- Does NOT make Z2 remedy decisions
- Does NOT close unknowns that Jester raised
- Does NOT contradict Witness/Witch/Warlock without strong reason
- Does NOT recommend specific fixes

---

## Synthesis Algorithm

### Phase 1: Jester Integration (Challenge Ingestion)

For each Jester challenge:

**Step 1a: Is the challenge valid?**

```
IF challenge points to a contradiction in Witness/Witch/Warlock:
    validity = "valid — data inconsistency detected"
ELIF challenge points to an ambiguity in the input:
    validity = "valid — interpretation ambiguity"
ELIF challenge asks about missing evidence:
    validity = "valid — unknowns raised"
ELIF challenge is speculative without evidence pointer:
    validity = "questionable — speculative; downgrades to low significance"
ELSE:
    validity = "unknown — requires Oracle judgment"
```

**Step 1b: What does it change?**

```
IF challenge is valid AND high-severity:
    impact = "could change mechanism, standing, or unknowns"
ELIF challenge is valid AND medium-severity:
    impact = "could refine one component of diagnosis"
ELIF challenge is valid AND low-severity:
    impact = "clarifies edge case; unlikely to affect remedy"
ELIF challenge is questionable or speculative:
    impact = "preserve as unknown; don't let it move diagnosis"
```

**Step 1c: Preserve unknowns**

```
If Jester raises a question that can't be answered from input:
    unknowns.append(challenge.question)
    DO NOT try to infer an answer
```

### Phase 2: Integration Into Steps 1–7

For each step (1–7), Oracle includes:

```
Step N:
  [Witness + Witch/Warlock findings for this step]

  [IF any Jester challenge targets this step:]
    Jester Challenge J_X: "[question]"
    Oracle Response:
      - Is it valid? [yes/no/partial]
      - Does it change the finding? [how?]
      - What unknowns does it raise? [list]

  [Final finding for Step N, incorporating Jester inputs]
```

### Phase 3: Integration Into Extensions A–E

**Extension A: Epistemic Status**

```
Jester challenges on Extension A often ask: "How do you know this is OBSERVED vs. INFERRED?"

Oracle response:
  - If Jester raises valid doubt about epistemic status, downgrade (INFERRED → UNKNOWN)
  - If Jester provides no new evidence, keep Witness classification
  - Do NOT upgrade status (INFERRED → OBSERVED) based on Jester reasoning
```

**Extension B: Temporal State**

```
Jester challenges on Extension B often ask: "Did this boundary exist at event time? How do you know?"

Oracle response:
  - If Jester raises valid ambiguity about temporal state, mark as UNKNOWN at event time
  - Keep "current state" separate from "state at event time"
  - If temporal state can't be determined, preserve as unknown
```

**Extension C: Evidence Independence**

```
Jester challenges on Extension C often ask: "Are these really two independent pieces or one with redundancy?"

Oracle rules:
  - If two pieces come from same system, they share provenance (one piece, two logs)
  - If Jester questions whether a piece is independent, verify against original input
  - If verification is impossible, mark as PARTIALLY_DEPENDENT (not fully independent)
```

**Extension D: Reversibility & Exposure**

```
Jester challenges on Extension D often ask: "Is the consequence still active? Prove it's contained."

Oracle response:
  - If Jester raises doubt about whether consequence is reversed, mark as PARTIALLY_REVERSED or UNKNOWN
  - Do NOT claim containment unless evidence is strong
  - If organizational exposure is mentioned (downstream artifacts), preserve as unknown/unresolved
```

**Extension E: Counterfactual Control**

```
Jester challenges on Extension E often ask: "Would your proposed control actually work?"

Oracle response:
  - If Jester's challenge to counterfactual is valid, revise the control
  - If Jester proves counterfactual wrong, say "this control is insufficient; another layer needed"
  - Do NOT weaken counterfactual based on Jester speculation; require evidence
```

### Phase 4: Mechanism Synthesis

Mechanism is **non-exclusive** (multiple failure categories can apply simultaneously).

```
Base mechanism (from Witness + Witch/Warlock):
  [List: BOUNDARY-FAILURE, CUSTODY-BREAKDOWN, BEHAVIOR-DEVIATION, ...]

For each Jester challenge that targets mechanism:
  IF challenge suggests alternative mechanism:
      Add it to list (mechanisms are non-exclusive)
  ELIF challenge questions whether mechanism applies:
      Downweight it (note "uncertain whether this mechanism applied")
  ELIF challenge splits mechanism into sub-components:
      Refine list (e.g., "CUSTODY-BREAKDOWN" → "decision-custody only" vs. "full collapse")
```

**Example (IC-063):**

```
Witness/Witch/Warlock mechanism:
  ["BOUNDARY-FAILURE", "CUSTODY-BREAKDOWN", "MEASUREMENT-ERROR"]

Jester challenge J3: "You say signature verification prevents it. But the root of trust proof is still missing. Doesn't that fail the counterfactual?"

Oracle integration:
  Mechanism remains: ["BOUNDARY-FAILURE", "CUSTODY-BREAKDOWN", "MEASUREMENT-ERROR"]
  Add to unknowns: "Whether mechanism is fully mitigated (signatures prevent re-occurrence, but root of trust closure still needed)"

Oracle does NOT add "ROOT-OF-TRUST-UNRESOLVED" as a mechanism (that's a standing/remedy issue, not a mechanism)
```

### Phase 5: Standing Synthesis

**Standing = current state of mechanism + unknowns + reversibility**

```
Standing format: "[MECHANISM_STATUS] / [ROOT_OF_TRUST_STATUS] / [EXPOSURE_STATUS]"

MECHANISM_STATUS options:
  ABSENT           (no failures occurred; false alarm)
  PRESENT          (failures occurred; still active)
  MITIGATED        (failures occurred; post-incident controls prevent recurrence)
  PARTIALLY_MITIGATED (some controls in place; others missing)
  UNKNOWN          (can't determine if mitigated)

ROOT_OF_TRUST_STATUS options:
  ESTABLISHED      (external proof of authority; verified)
  UNRESOLVED       (no external proof; still depends on writable/uncontrolled surface)
  PARTIALLY_UNRESOLVED (partial external proof; some gaps remain)
  UNKNOWN          (can't determine)

EXPOSURE_STATUS options:
  CONTAINED        (consequence isolated; no spread)
  PARTIALLY_CONTAINED (immediate spread stopped; organizational exposure remains)
  ONGOING          (still spreading or impact still active)
  REVERSED         (consequence fully reversed; indicators scrubbed)
  UNKNOWN          (can't determine)
```

**For each Jester challenge that affects standing:**

```
IF challenge downgrades MECHANISM_STATUS:
    Update standing mechanism component (e.g., MITIGATED → PARTIALLY_MITIGATED)

IF challenge raises doubt about ROOT_OF_TRUST_STATUS:
    Update standing root-of-trust component (e.g., ??? → UNRESOLVED if doubts are valid)

IF challenge reveals additional EXPOSURE:
    Update standing exposure component (e.g., CONTAINED → PARTIALLY_CONTAINED)

IF challenge introduces unknowns that affect standing:
    Preserve unknowns explicitly in standing statement
```

**Example (IC-063):**

```
Witness + Witch/Warlock standing (before Jester):
  "MECHANISM_MITIGATED / ROOT_OF_TRUST_UNKNOWN / PARTIALLY_CONTAINED"

Jester Challenge J5: "If we fix the mechanism but the Z2 key enrollment ceremony never happens, have we solved IC-063 or just masked it?"

Oracle integration:
  This is a valid question about root of trust.
  If Jester is right that ceremony hasn't happened, we can't claim root of trust is RESOLVED.

Updated standing:
  "MECHANISM_MITIGATED / ROOT_OF_TRUST_UNRESOLVED / PARTIALLY_CONTAINED"

Add to unknowns:
  "Z2 key enrollment ceremony status: has it been performed with external third party?"
```

---

## Synthesis Rules (Non-Negotiable)

### Rule 1: Every Jester Challenge Must Appear in Output

```
IF a Jester challenge is raised:
    It must appear in the final Oracle diagnosis (in Steps 1–7, Extensions A–E, or Unknowns section)
    Oracle cannot ignore it

IF Oracle decides challenge is invalid:
    Diagnosis must say WHY it's invalid (e.g., "contradicts direct evidence in Witness Step 1")
    Not just dismissing it as "noise"
```

*Implementation note (v0.1 code): `src/oracle_agent/oracle.py`'s `run_oracle()` runs a
structural check after every call (`OracleOutput.missing_challenge_ids`) and logs a
warning if any Jester `challenge_id` is absent from `jester_integration`. This is a
mechanical floor, not a substitute for Z2 review -- it catches a dropped challenge_id,
not a challenge addressed in name only.*

### Rule 2: Unknowns Are Preserved, Not Inferred

```
IF Jester raises a question we cannot answer from input:
    Preserve it as UNKNOWN
    DO NOT speculate or infer an answer
    DO NOT mark it as "probably resolved because..."

Exception:
    If Witness/Witch/Warlock provide direct evidence that answers the unknown,
    cite that evidence and mark as OBSERVED/VERIFIED (with confidence level)
```

### Rule 3: Contradictions Are Noted, Not Hidden

```
IF Jester challenge contradicts Witness/Witch/Warlock finding:
    Note the contradiction explicitly in the diagnosis
    Do NOT hide it in a footnote
    Evaluate both sides: which has stronger evidence?
    If evidence is equal, preserve contradiction as unknown
```

### Rule 4: Downgrades Are Justified, Upgrades Are Forbidden

```
ALLOWED: Downgrade confidence based on Jester challenge
  - OBSERVED → INFERRED (if Jester raises doubt about observability)
  - MITIGATED → PARTIALLY_MITIGATED (if controls are incomplete)
  - MECHANISM_[X] → MECHANISM_[X] UNCERTAIN (if mechanism is questionable)

NOT ALLOWED: Upgrade confidence based on Jester reasoning
  - INFERRED → OBSERVED (Jester can't create evidence, only question it)
  - UNKNOWN → RESOLVED (without new evidence from input)
  - Dropping an unknown because "it probably doesn't matter"
```

### Rule 5: Remedy Scope Is Oracle's Job; Remedy Decision Is Z2's Job

```
Oracle does:
  - Estimate remedy scope (e.g., "10 points" = 10 distinct fixes needed)
  - List those fixes (e.g., "1. Ratify invariant, 2. Move key enrollment external, ...")
  - Note dependencies (e.g., "Fix #3 blocks fix #4")

Oracle does NOT:
  - Decide which fixes to implement (Z2 decides)
  - Recommend priority order (Z2 decides)
  - Commit to timelines (Z2 decides)

Example remedy scope statement:
  "Remedy requires 10 points of work, including [list].
   Z2 must decide which points to implement and in what order.
   Oracle assessment: all 10 are required for full standing closure."
```

### Rule 6: Jester Challenges Don't Affect Scope Estimation

```
IF Jester raises a challenge:
    Does it add a new fix requirement? Only if Oracle determines it's a separate mechanism.
    Most Jester challenges refine existing findings, not add new requirements.

Example (IC-063):
  Jester J1: "Is 'boundary absent' distinct from 'never designed'?"
    Oracle: Both require "design + implement mechanical boundary" → same remedy point
    Scope: Still 10 points; J1 doesn't add a new point

  Jester J5: "If ceremony never happens, is it solved?"
    Oracle: This highlights that "Z2 key-enrollment ceremony" is critical
    Scope: Already in remedy point #3; J5 strengthens it, doesn't add it
```

---

## Oracle Prompt (v0.1)

This is the prompt implemented in `src/oracle_agent/oracle.py`:

```
You are the Oracle in a Lawson Diagnostic Audit.

Your role: Synthesize Witness + Witch/Warlock + Jester inputs into a single diagnosis.

CONSTRAINTS:
- You do NOT make Z2 remedy decisions (say "Z2 must decide")
- You do NOT close unknowns Jester raised
- You do NOT contradict Witness/Witch/Warlock without strong evidence
- You do NOT recommend specific fixes (that's Z2's job)
- You acknowledge every Jester challenge in your diagnosis

INPUTS:
1. Witness findings (Steps 1–3, Extensions A–D)
2. Witch/Warlock findings (Steps 4, 7, mechanisms)
3. Jester challenges (JSON array; 3–5 questions)

YOUR TASK:
For each Jester challenge:
  A. Decide: Is it valid? Does it point to something Witness/Witch/Warlock missed?
  B. Integrate: Where does it fit in Steps 1–7 or Extensions A–E?
  C. Preserve: What unknowns does it highlight?

Then synthesize a complete diagnosis covering Steps 1–7, Extensions A–E, mechanism,
standing, unknowns, and remedy scope.

RULES (HARD LIMITS):
1. Every Jester challenge appears in diagnosis
2. Unknowns raised by Jester are preserved (not inferred away)
3. Contradictions are noted, not hidden
4. Confidence can downgrade, not upgrade
5. Remedy scope is Oracle's job; decision is Z2's
6. Jester challenges don't automatically add scope points (they refine existing findings)

TONE:
Clear, forensic, precise. You are speaking to Z2 (decision-maker). Z2 trusts you because:
  1. You addressed every Jester challenge
  2. You preserved every unknown Jester raised
  3. You didn't speculate beyond evidence
  4. You made remedy scope clear (who decides what)
```

*Deviation from the v0.1 design brief: the code does not ask the model to also render
the PR #3 markdown. `src/oracle_agent/render.py` renders it deterministically from the
structured JSON instead, so the D4 PR template holds exactly even when the model's
prose varies between runs.*

---

## Measurement (M4: Synthesis Quality)

**Definition:** % of Oracle diagnoses later confirmed or used by Z2 remedy decision

**How to measure:**
- After Z2 makes remedy decision, ask: "Did the Oracle diagnosis inform your remedy decision?"
- Log responses: "fully used" (80–100%) / "partially used" (40–80%) / "not used" (<40%)
- M4 = % of audits where Oracle was "fully used" + 0.5 × % "partially used"

**Target:** M4 ≥ 80%

**Example (IC-063):**
```
Oracle diagnosis: MECHANISM_MITIGATED / ROOT_OF_TRUST_UNRESOLVED / PARTIALLY_CONTAINED
  with 10 remedy points

Z2 decision: Implement remedy points #1, #2, #3, #5 this sprint; defer #4, #6–#10 to next cycle

M4 assessment: Oracle diagnosis was "partially used" (Z2 selected subset of points but logic was sound)
  Score: 0.5 × "partially used" = 0.5
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-09-24 | Baseline synthesis algorithm, rules, and prompt. Five-phase integration. |
| 0.1 (code) | 2026-09-25 | Implemented as a strict-schema tool call in `src/oracle_agent/oracle.py`; Rule 1 gets a mechanical structural check (`missing_challenge_ids`); markdown rendering moved to deterministic code (`render.py`) rather than model output. |
