# Debugging, for agents

Goal: find the root cause with evidence, fix it once where every caller benefits,
and prove the fix with the same check that showed the bug.

Read `references/tdd.md` too: the fix half of this file is its loop.

## 1. Build the loop before the theory

Before reading code to form a theory, get **one command** that goes red on the
user's exact symptom: a failing test, a curl, a CLI call with a fixture, a
script that replays a captured payload. Run it and keep the output.

- It must show the symptom the user reported, not a different failure nearby.
- Make it fast and deterministic (pin time, seed randomness, isolate files).
  For a flaky bug, loop it until the failure rate is high enough to work with.
- If no loop is possible, stop and say what you tried and what you need
  (access, a log, a captured request). Do not guess-and-patch.

## 2. Is it even running your code?

Half of "the fix didn't work" is the old code still running. Check these before
the next hypothesis:

- **Installed copy vs source.** Plugins, packages and globally installed CLIs run
  a copy. Editing the repo changes nothing until reinstall (and, for Claude Code
  plugins, a version bump and restart).
- **PATH order.** `type -a <cmd>` lists every copy. An old symlink earlier on PATH
  wins over the new one.
- **Stale deploy.** Edge platforms can serve the previous build for a minute or
  two after a deploy. Check the serving version, wait, retest.
- **Config not reloaded.** `docker restart` does not re-read `.env`;
  `docker compose up -d` recreates changed containers. Many servers read env
  only at start.
- **Wrong target.** The deploy went to another account, project or environment
  than you think. Print the target (`wrangler whoami`, the project id, the
  branch-to-env mapping) before trusting a result.
- **Env var "missing".** A secret empty in your shell may only be injected into
  the process. Check how the process gets it, without printing the value.

## 3. Find the cause, not a symptom

- Change one thing at a time and re-run the loop after each change.
- Say each hypothesis out loud with the evidence that would kill it, then run
  that check. Keep the ones that survive, with `file:line`.
- Diagnosis and fixing are separate steps. Helpers or subagents asked to find the
  cause return the cause with evidence, not a patch.
- Trust the live system over the docs and the repo: the deployed schema, the
  serving version, the actual env. Docs describe intent.
- "Completed" is not "worked". A job that swallows its own failure reports
  success forever. Look at what it produced, not its status.
- Before calling data empty or dead, count it for real. Planner statistics can
  say zero rows on a full table.

## 4. Fix it once

- Grep every caller of the function you are about to change. A guard in the
  shared function is one change; a guard in the caller the ticket names leaves
  the siblings broken.
- Write the failing test first (`references/tdd.md` section 3), then the fix,
  then re-run the original loop from step 1. It must go green on the user's
  exact symptom.
- Remove temporary logging and debug flags you added.
- Cap it at three full cycles (hypothesis, check, fix). Then stop and report
  what you ruled out and what you would try next.

## 5. Report

- The symptom, the loop command, and its red output.
- The root cause with `file:line`, and what ruled out the other hypotheses.
- The fix, the test that covers it, and the loop's green output.
- Any sibling caller or neighbouring system with the same flaw.
