---
name: grill
description: Batch-grill a written plan, spec or design doc before building it. Use when the user says grill this, grill the plan, stress-test this, poke holes in this, find the gaps in this plan, what did I miss, is this plan solid, challenge this design, play devil's advocate, batch grill, red-team this plan, or before implementing any plan or spec. Runs up to five unattended rounds in which an adversary attacks the plan and every attack is settled from source, then asks the user once, in a single batch, only the questions the agent could not answer itself. Not for reviewing a code diff.
---

# grill

Input: a written plan file. If the plan only exists in chat, write it to a file first.

## Rounds 1-5, unattended

Each round:
1. Send `references/adversary-prompt.md` to an adversary that cannot edit:
   a general-purpose subagent told it is read-only, or, when the `codex` CLI is
   installed, `codex exec -s read-only "<the prompt>"`.
2. Settle every item yourself from source (read the file, run the command, check
   the docs). Each ends in one state:
   - **Resolved**: the answer, with file:line.
   - **Plan changed**: the attack landed; edit the plan, note what changed.
   - **Needs user**: intent, priority, spend, or outside knowledge only. A fact
     you could look up never goes here.
3. Stop early when a round raises nothing new.

## Round 6, one batch to the user

Send every "needs user" item in ONE message:

    Q<n> - <title>: <question, with options>
    Why source could not settle it: <one line>
    Recommendation: <pick and why>

Nothing gets implemented while one is open. Round 7 runs only if the answers
change the plan's structure; it is the ceiling.

## Verdict, appended to the plan

    ## Grill verdict - YYYY-MM-DD
    - Rounds: N (self) + N (user)
    - Attacks raised: N - resolved: N, changed the plan: N, escalated: N
    - Plan changes: one line each
    - Accepted risks: what is knowingly unhandled, and why that is fine
    - Unresolved: anything open, and what would settle it

Recount the numbers before writing them. An empty "accepted risks" on a real plan
means the grill was theatre.
