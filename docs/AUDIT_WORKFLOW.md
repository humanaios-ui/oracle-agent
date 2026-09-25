# Audit Workflow (Z1 + Z2 instructions)

1. Write `audits/<INCIDENT-ID>/01-WITNESS.md` (Steps 1-3, Extensions A-D) and open PR #1.
2. Write `audits/<INCIDENT-ID>/02-WITCH_WARLOCK.md` (Steps 4, 7, custody/mechanism analysis) and open PR #2.
   In the PR #2 description, include a line like `Witness: #1` so the workflow can attribute the Witness PR correctly.
3. Merge PR #1, then PR #2. Merging PR #2 triggers `.github/workflows/oracle-audit.yml`.
4. Oracle Agent runs Jester then Oracle and opens a draft PR #3 (`audits/<INCIDENT-ID>/03-JESTER_ORACLE.md`), labeled `awaiting-oracle-review`.
5. Z2 reviews PR #3. Oracle's diagnosis is advisory and diagnostic, not binding:
   - Merge PR #3 as-is, optionally with a dissent note, or
   - Comment requesting revision and re-run manually with edited inputs, or
   - Override the standing and record why in `REGISTERED.md`.
6. Remedy selection and execution remain a Z2 decision, tracked separately in `REGISTERED.md` / `PRIORITY_QUEUE.md`.

## Manual run (no GitHub Action)

```bash
python -m oracle_agent.cli \
  --witness audits/IC-063/01-WITNESS.md \
  --witch-warlock audits/IC-063/02-WITCH_WARLOCK.md \
  --incident-id IC-063 \
  --out audits/IC-063/03-JESTER_ORACLE.md
```

## Secrets and variables required

- Repository secret `ANTHROPIC_API_KEY` — required for `oracle-audit.yml` to run.
- Repository variable `ORACLE_REVIEWER` (optional) — a GitHub username to auto-assign PR #3 to.

## Known limitation

`oracle-audit.yml` extracts the Witness PR number by regex-matching `Witness: #<N>` /
`Witness PR #<N>` in the Witch/Warlock PR's body. If that line is missing, PR #3's
"Based on" line will only cite the Witch/Warlock PR. This is a deliberate v0.1
simplification rather than an API lookup chain across PRs — revisit if it proves
unreliable in practice (Jester precision measurement, M3, is a proxy for whether
this matters).
