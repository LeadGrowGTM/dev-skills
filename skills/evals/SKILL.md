---
name: evals
description: Write and run evals, and hill-climb skills and prompts against them. Use when the user wants evals or test cases for a prompt, agent, skill or plugin, asks whether a change made it better or worse, wants to measure how often a skill triggers or which skill fires on which phrasing, wants to mine real phrasing from session logs into test cases, or wants to tune (hill-climb) a skill description or prompt against a held-out set. Covers claude plugin eval cases, graders, cost and CI.
---

# evals

Pick the job, read its reference.

| Job | Read |
|---|---|
| Write or run `claude plugin eval` cases and graders | `references/plugin-eval.md` |
| Turn session logs into test cases | `references/mining.md` |
| Tune skill descriptions against the cases | `references/hillclimb.md` |

Scripts in this skill's directory (stdlib Python, take `--plugin DIR`):
`scripts/new_case.py` (one confusion-matrix case), `scripts/mine.py` (logs to
candidates), `scripts/propose.py` (candidates to proposed cases),
`scripts/make_cases.py` (reviewed proposals to cases), `scripts/climb.py` (tune
descriptions; `report` checks a result against thresholds).

Rules every time:
- Hold out 40% of cases (the split is fixed by slug hash) and judge only on hold.
- Trigger tests run with `--ablation none`; a no-plugin baseline means nothing there.
- Say the spend before running a paid pass, and pass `--max-cost-usd`.
- Mined cases are reviewed by a human before commit; raw logs never leave the machine.
