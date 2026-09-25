# IC-063 Lawson Diagnostic Audit — Witch/Warlock

## Step 4: Custody Topology
Read, write, and decision custody collapsed onto a single observable surface at
incident time: the authenticated humanaios-ui GitHub account. No mechanism
separated "who can post content" from "who holds Z2 decision authority".

## Step 7: Mechanism
Non-exclusive failure list:
1. BOUNDARY-FAILURE -- no mechanical decision boundary existed
2. CUSTODY-BREAKDOWN -- read/write/decision custody were not separated
3. MEASUREMENT-ERROR -- the system measured GitHub account identity instead of
   Z2 authority proof

Counterfactual control test: adding signature verification catches unsigned
claims going forward, but does not by itself establish that the Z2 signing key
has independent, externally-verifiable provenance -- the root of trust would
still depend on a writable surface (this repository) unless a separate
key-enrollment ceremony is performed outside of it.

## Assumptions That Could Be Wrong
- That GitHub account activity logs are a reliable proxy for authorial intent.
- That the Z2 key currently in node_key_registry.json was enrolled through a
  process independent of the account it now verifies.

## Unknowns Raised by Witch/Warlock Analysis
- Whether the Z2 key-enrollment ceremony has ever been performed with an
  external, independent party.
