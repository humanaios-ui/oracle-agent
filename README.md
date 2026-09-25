# Oracle Agent

Automates the **Jester** and **Oracle** phases of a Lawson Diagnostic Audit (OI-ORACLE-01).

Given a Witness PR and a Witch/Warlock PR for an incident, Oracle Agent:

1. Runs **Jester** — generates 3-5 adversarial challenges against the Witness/Witch-Warlock findings.
2. Runs **Oracle** — synthesizes Witness + Witch/Warlock + Jester into a single diagnosis (mechanism, standing, preserved unknowns, remedy scope).
3. Renders PR #3 markdown, ready for Z2 review.

Oracle Agent never makes the remedy decision, never closes an unknown Jester raised, and never recommends a specific fix — see `docs/ORACLE_SYNTHESIS_RULES.md`.

## Quick start

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...  # or `ant auth login`

python -m oracle_agent.cli \
  --witness audits/IC-063/01-WITNESS.md \
  --witch-warlock audits/IC-063/02-WITCH_WARLOCK.md \
  --incident-id IC-063 \
  --out audits/IC-063/03-JESTER_ORACLE.md \
  --witness-pr 1 --witch-warlock-pr 2
```

Or as an MCP tool:

```bash
python -m oracle_agent.main
```

## Repository layout

- `src/oracle_agent/` — the service (`jester.py`, `oracle.py`, `render.py`, `cli.py`, `main.py`)
- `tests/` — mocked unit tests (default) + an optional live end-to-end test gated on `ANTHROPIC_API_KEY`
- `docs/` — the ratified design: audit workflow, Jester prompt design, Oracle synthesis rules
- `.github/workflows/oracle-audit.yml` — triggers PR #3 generation when a Witch/Warlock PR merges
- `.github/workflows/test.yml` — runs the mocked test suite on push/PR

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Anthropic API credential |
| `ORACLE_AGENT_MODEL` | `claude-opus-5` | Model used for both Jester and Oracle calls |
| `ORACLE_AGENT_MAX_TOKENS` | `8000` | Max output tokens per call |

## Status

Design ratified under OI-ORACLE-01 (D1 service architecture; D2 deployment = GitHub Actions + this repo). See `docs/AUDIT_WORKFLOW.md` for the end-to-end process.
