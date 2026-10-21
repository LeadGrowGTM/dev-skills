# Test-first, for agents

Goal: every behaviour the task names ends up as code plus a check that fails
without it, and the claim "it works" rests on output you actually ran.

Plain TDD advice (red, green, vertical slices, test at the public interface) is
covered well elsewhere. This file is about the ways an agent's test loop goes
wrong, each seen on real runs, and the rule that stops it.

## 1. Read before you write

- Read the task's requirements, then `CLAUDE.md`, `AGENTS.md` and `CONTEXT.md`
  if present, then the code the change touches and **every caller** of anything
  you will modify. A fix in a shared function is one guard; a fix in the one
  caller the ticket names leaves the others broken.
- Find the existing test file, fixture and helper for this area and reuse them.
  A second test harness next to the first is the most common slop.

## 2. Baseline the feedback loop

Find the verification command: the one the task names, otherwise the repo's
test, type-check and lint scripts (`package.json` scripts, `Makefile`,
`pyproject.toml`, CI workflow). Run it **once before editing** and keep the
output. Without a baseline, a test that was already red gets blamed on you, or
your red gets waved off as "pre-existing".

If the repo has no single command, write one (`scripts/green.sh`: tests, lint,
type-check, `set -euo pipefail`) and say so. One command is what makes
"green" checkable by someone else.

## 3. Red, then green, one slice at a time

For each behaviour:
1. Write one failing test at the public seam (the function, route, CLI or
   component people call, not a private helper).
2. Run it and watch it fail **for the right reason**: the assertion, not an
   import error or a typo. A test that never failed proves nothing.
3. Write the minimum code that passes it. Run the test again.
4. Next behaviour.

- **Bug fix:** the first test reproduces the bug as reported, and fails. Then fix.
  If you cannot make it fail, you have not found the bug yet.
- **Expected values** come from the spec, a worked example or a known-good
  literal, never recomputed the way the code computes them
  (`expect(add(a, b)).toBe(a + b)` passes by construction).
- **How much to test:** trivial one-liners need none. Non-trivial logic (a
  branch, a loop, a parser, money, auth, anything that deletes) ships at least
  one check. No per-function suites unless asked.

## 4. Green for real

These are the ways agents reach green without fixing anything. None of them count.

| Shortcut | Rule |
|---|---|
| Edit the assertion to match the wrong output | The test changes only if the spec says the old expectation was wrong. Say which line of the spec. |
| `skip`, `xfail`, `.only`, `@ts-ignore`, `# noqa`, `eslint-disable`, lowered coverage threshold | Checks stay as strict as you found them. |
| Special-case the test input in the code (`if input == "fixture"`) | The fix goes in the general path. |
| Mock the thing under test | Mock only what you do not own (network, clock, paid APIs). |
| Catch and swallow the error so the test passes | A failure must stay visible: throw, or return an error the test asserts on. |
| Delete the failing test | Only with the user's say-so, and say it in the report. |

Stop after **three honest attempts** on the same red. Report what you tried and
what you learned. A fourth attempt at 2 a.m. is how the shortcuts above happen.

## 5. Prove it, do not describe it

- Run the full verification command at the end, not just the new test. Keep the
  real output (the last lines with the pass/fail counts).
- "Tests pass" in a report is a claim. A pasted output block can be typed by
  anyone. If the work goes to a reviewer or CI, the proof is the command they
  can re-run, or a log the tooling wrote, not text inside the report.
- If a check could not run (no database, no network, paid API), say so plainly
  and name what would run it. Never round "did not run" up to "passed".
- When a script or hook can enforce a rule, prefer it to a sentence in a prompt.
  Prompt-only rules were skipped on real runs: "work in a worktree" was ignored
  until a script refused a second writer on the same directory.

## 6. Report

- Each requirement, the test that covers it (file:line), and the code that
  satisfies it.
- Baseline result, final result (real output), and anything that was already red.
- Tests changed or removed, and why.
- What could not be verified here, and what would verify it.
