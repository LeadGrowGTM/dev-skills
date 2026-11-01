# Writing documents an agent reads

The levers below decide whether an agent-consumed document is predictable. They
apply to a skill body, a `references/` file, and an `AGENTS.md` line equally: the
packaging differs, the writing does not. An agent takes the same *process* every
run rather than producing the same output, so the document has to shape the
process.

Adapted from Matt Pocock's `writing-for-agents` skill
(`skills/productivity/writing-for-agents`, upstream
`github.com/mattpocock/skills` at `4ae2317`, MIT, Copyright (c) 2026 Matt Pocock).
The frontmatter and invocation mechanics are dropped here because
`plugin-eval.md` and `CONTRIBUTING.md` already own how this plugin's skills are
declared and versioned; what follows is the writing itself.

## Context pointers

A **context pointer** is a reference in the agent's context naming out-of-context
material and encoding the condition for reaching it. A skill description is one;
a line in `AGENTS.md` naming a doc is the same object. The pointer's *wording*,
not its target, decides when the agent reaches the material and how reliably. A
must-have target behind weak wording is a variance bug: sharpen the wording
first, and inline the material only if sharpening fails.

A pointer does two jobs: say what the material is, and list the **branches** that
should trigger reaching it. Because every always-loaded pointer costs on every
turn, it earns harder pruning than the body it points at:

- **Front-load the leading word**, since the pointer is where the triggering work
  happens.
- **One trigger per branch.** Synonyms renaming one branch are that branch
  written twice; collapse them.
- **Cut identity the body already carries.**

This is the whole basis of a skill description in this plugin: it is a pointer,
and the trigger evals in `evals/` are how a pointer's wording gets graded rather
than guessed. A description change is a hypothesis about a trigger, and the
confusion matrix is the test.

## The two loads

- **Context load** is what always-loaded material costs on the window: a
  description, an `AGENTS.md` line, anything present every turn whether or not it
  fires.
- **Cognitive load** is what the documents cost the human, who is the index of
  which exists and when to reach for each. Not a cost to minimise: it is the price
  of human agency. Spend it where human judgement matters.

Material reached only through a pointer escapes context load at the price of the
pointer's own line. Material with no pointer at all rides entirely on cognitive
load.

## Information hierarchy and progressive disclosure

A document mixes two content types: **steps** (ordered actions the agent
performs) and **reference** (definitions, rules and facts consulted on demand).
Both are legitimate, all-steps (a recipe), all-reference (a review's rules), or a
mix. The decision is where each piece sits on a ladder ranked by how immediately
it is needed:

1. **In-file step**, the primary tier: what the agent does, in order.
2. **In-file reference**, consulted on demand. A flat peer-set where every rule of
   a review sits on one rung is a fine arrangement, not a smell.
3. **Disclosed reference**, pushed into a separate file behind a pointer, loaded
   only when the pointer fires.

Push too little down and the top bloats; push too much and you hide material the
agent needs. **Progressive disclosure** is the move down the ladder so the top
stays legible. Branching is the cleanest disclosure test: inline what every branch
needs, disclose what only some branches reach. When a document has steps, in-file
reference that should be disclosed buries them and turns attending to them into a
coin-flip.

**Co-location** is the within-file companion: keep a concept's definition, rules
and caveats under one heading rather than scattered, so reading one part brings
its neighbours. Grouped material reads like documentation written for the agent.

**Sprawl** is the failure: a document too long even when every line is live.
Attention thins across the excess. The cure is the ladder, plus splitting by
branch or sequence so each path carries only what it needs.

## Steps and completion criteria

Every step ends on a **completion criterion**: the condition that says the work is
done. Two properties make it a lever.

- **Clarity**: can done be told from not-done? A vague bound invites **premature
  completion**, where attention slips to being done. The visible steps still ahead
  supply the pull; the criterion's clarity is the resistance. Defend by sharpening
  the bound first, which is local and cheap; only if it is irreducibly fuzzy *and*
  the rush is observed, hide the later steps by splitting the sequence. Hiding only
  works across a real context boundary (a hand-off or a dispatch); an inline call
  leaves the later steps in context and clears nothing.
- **Demand**: how much the criterion requires. "Every modified model accounted
  for" forces thorough work where "produce a change list" does not. Demand drives
  the **legwork** the agent does inside the work, and it is not step-bound:
  "every rule applied" binds a body of flat reference the way "every step done"
  binds a sequence. That is how an all-reference document still carries an
  exhaustiveness bar.

The strongest criteria are both checkable and exhaustive.

## Leading words

A **leading word** is a compact concept already living in the model's pretraining
that the agent thinks with while running the document (*lesson*, *fog of war*,
*tracer bullets*, *red*). Repeated as a token, never as a sentence, it accumulates
a distributed definition and anchors a whole region of behaviour in the fewest
tokens.

It anchors twice. In the body, execution: the agent reaches for the same behaviour
whenever the word appears. In a pointer, invocation: when the same word lives in
the prompts, the docs and the code, the agent links that shared language to the
material and reaches it more reliably.

Hunt for the chance to refactor with leading words. A triad spelled out at three
sites, or a pointer spending a sentence to gesture at one idea, is a passage
begging to collapse: "fast, deterministic, low-overhead" -> *tight*; "a loop you
believe in" -> *red*, which turns a fuzzy gate into a binary observable state.
Fewer tokens, and a sharper hook. Assume every document is carrying restatements a
leading word would retire.

**Negation** is the failure mode beside this lever: steering by prohibition drags
the forbidden behaviour into context and makes it more available. *Don't think of
an elephant.* Prompt the positive: state the target behaviour so the banned one is
never spoken. A prohibition earns its place only as a hard guardrail that cannot
be phrased positively, and even then pair it with the positive target.

## Pruning

- **Single source of truth**: one authoritative place per meaning, so changing
  behaviour is a one-place edit. **Duplication** costs maintenance and tokens and
  inflates a meaning's prominence past its real rank. (The accidental inverse of a
  leading word, which repeats a token deliberately, never the meaning.)
- The **environment** is a source of truth too (`package.json` scripts, config,
  the directory layout, `--help`). A document restating it is a **cache**, earning
  its load only where the lookup is expensive. Cache the unwritten convention, the
  reason behind a choice, the gotcha no config confesses; leave one-file,
  one-command lookups to the environment, where they cannot go stale.
- **Relevance**: does the line still bear on what the document does? Lines lose
  relevance by never bearing on the task, or by going stale. Without pruning the
  default fate is **sediment**: stale layers that settle because adding feels safe
  and removing feels risky, until you must core down through them to find what is
  live.
- Hunt **no-ops** sentence by sentence: an instruction the model already obeys pays
  load to say nothing. The test is model-relative, not reader-relative, so two
  people disagreeing about a no-op disagree about the default and settle it by
  running the document rather than debating. When a sentence fails, delete the
  sentence rather than trimming words from it. The test also grades leading words:
  a word too weak to beat the default (_be thorough_ when the agent is already
  thorough-ish) is a no-op, and the fix is a stronger word (_relentless_), not a
  different technique.

## Applying this to a plugin skill

- The description is a pointer: trigger branches only, front-loaded.
- The `SKILL.md` body is steps plus a router table; everything branch-specific
  lives in `references/` behind that table.
- A rule belongs here only if it changes behaviour against the default. Anything
  the model already does is a no-op, and costs load to say.
- After editing any description, re-run the trigger evals in the README. The
  confusion matrix is the completion criterion for a description change.

## ATTRIBUTION

Adapted from `github.com/mattpocock/skills`
(`skills/productivity/writing-for-agents`, SKILL.md and SKILL-MECHANICS.md) at
`4ae2317`, MIT licensed.

MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
