# The design tree and its frontier

The grill asks a batch of questions per round. This file supplies the structure
that decides **which** questions belong in a round: without it, a round is
whatever the model happened to think of, and questions that depend on unsettled
answers get asked too early, where the answer is a guess.

Adapted from Matt Pocock's `grilling` skill (`skills/productivity/grilling`,
upstream `github.com/mattpocock/skills` at `4ae2317`, MIT, Copyright (c) 2026 Matt
Pocock). The adversary loop in `SKILL.md` is this plugin's own and is unchanged;
this file adds the tree and the frontier, which the flat round list did not model.

## The tree

Model the plan as a **design tree**: every decision branches into the decisions
that hang off it. "Which store holds the sessions" branches into "what evicts an
entry", which branches into "what happens to in-flight requests on eviction". The
tree is a dependency structure, not a topic list: an arrow means the child's
answer is only meaningful once the parent's is settled.

## The frontier

The **frontier** is every decision whose prerequisites are already settled: the
questions answerable *now* without guessing at answers nobody has given yet.

Ask the whole frontier in one round, numbered, each with a recommendation. Then
stop and wait. A question whose answer depends on another question still open in
this round belongs to a **later** round, not this one - asking it early is how a
grill produces answers that quietly contradict each other three rounds later.

Each round's answers reshape the tree: settled decisions push the frontier
outward and unblock questions that depended on them. Recompute the frontier after
every round rather than working a pre-written list.

## Facts are never frontier questions

Finding a fact is the agent's job, never the person's. When a frontier question
needs something from the environment (a file, a command, the docs), look it up or
dispatch the lookup; do not ask.

Don't block on it either: a running exploration is an unsettled prerequisite, so
only the questions downstream of it wait. Ask the rest of the frontier now.

The decisions are the person's. Put each to them and wait.

## How this meets the adversary rounds

The two mechanics compose, and they are not the same axis:

- The **adversary** finds what is wrong with the plan as written. It is a
  generator of attacks, settled from source in rounds 1-5 of `SKILL.md`.
- The **frontier** decides what to ask the person, and when. It is the gate on
  the batch in round 6.

An attack that needs a person's intent or priority becomes a **frontier
question** and waits for the round where its prerequisites are settled. An attack
that source can settle never reaches the person at all: resolve it, or change the
plan.

## Round format

Number every question and attach a recommendation, so a "yes" accepts it:

```
Q1 - <title>: <question, with the options>
Why source could not settle it: <one line>
Recommendation: <pick, and why>
```

Word each question so "yes" accepts the recommendation. One question per decision
on the frontier, no re-batching of a branch that is already settled.

## Done

The session is done when the frontier is empty: every branch of the tree visited,
nothing left silently assumed. Do not act on the plan until the person confirms
the shared understanding - an empty frontier is the completion criterion, and a
non-empty one that was never asked is the failure this file prevents.
