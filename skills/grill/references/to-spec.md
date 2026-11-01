# Writing the spec, after the grilling stops

Once the questions are settled, the thinking has to land somewhere durable that a
later session can act on without re-interviewing anyone. This is that step: pure
synthesis, no new interview. If gaps remain, go back to [grilling] rather than
inventing answers here.

Adapted from Matt Pocock's `to-spec` skill (`skills/engineering/to-spec`,
upstream `github.com/mattpocock/skills` at `4ae2317`, MIT, Copyright (c) 2026 Matt
Pocock). Two upstream steps were removed because they assume a personal issue
tracker and a human operator: publishing to a tracker, and the
`/setup-matt-pocock-skills` prerequisite. Here the spec is a file, and its
destination is the task's own brief or issue.

## 1. Ground it in what already exists

Read the code the change touches, plus its callers. Use the project's own
vocabulary - the words its files, symbols and docs already use - rather than
inventing names, and respect any recorded decision in the area.

## 2. Pin the seams before writing the spec

Choose the points where the feature will be tested. Prefer existing seams to new
ones, and the highest seam available (the outer boundary people actually call,
not a private helper). If a new seam is genuinely needed, propose it at the
highest point you can. Fewer seams across the codebase is better; one is the
ideal.

Write the chosen seams into the spec and flag them, because a spec whose seams
are wrong produces tests that pin the implementation instead of the behaviour.

## 3. Write the spec

Use this shape. Drop a heading only when it is genuinely empty; an empty "Out of
Scope" on a real spec means the boundary was never drawn.

```
## Problem statement
The problem, from the user's perspective.

## Solution
The solution, from the user's perspective.

## User stories
A long numbered list, each "As an <actor>, I want <feature>, so that <benefit>",
covering every aspect of the feature rather than the happy path alone.

## Implementation decisions
The modules built or modified, their interfaces, schema changes, API contracts
and specific interactions, plus any technical clarification the grilling settled.
No file paths and no code snippets: they go stale fastest of anything here.

Exception - if a prototype encoded a decision more precisely than prose can
(state machine, reducer, schema, type shape), inline that snippet under the
relevant decision and say it came from a prototype. Trim to the decision-rich
parts, not a working demo.

## Testing decisions
What makes a good test here (external behaviour, not implementation details),
which modules get tested, and the prior art in the codebase for each kind.

## Out of scope
What this deliberately does not cover.

## Further notes
Anything else a later reader needs.
```

## 4. Hand it on

Write the spec where the work will read it - the task's brief or the issue the
work came from - and state plainly that it is ready to be sliced. Do not start
implementing from the spec in the same breath: slicing comes next
(`references/to-tickets` in this plugin's sibling skills, or the tracker's own
fragmentation), and each slice should be a thin end-to-end path rather than a
layer.

## Anti-patterns

- **Interviewing again.** This step synthesises settled decisions; re-opening them
  wastes the grilling that already happened.
- **Restating the conversation.** The spec is what a reader needs to act, not a
  transcript with the interesting parts buried.
- **Paths and snippets.** They rot within a week; name the module and the
  interface instead.
- **A spec with no seams.** The tests then have nowhere good to live, and the
  implementation decides them by accident.
