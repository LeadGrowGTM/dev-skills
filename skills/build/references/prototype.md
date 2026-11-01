# Prototype

A prototype is **throwaway code that answers one design question**. The question
decides the shape. It is finished when the question is answered, and the answer,
not the code, is what survives.

Adapted from Matt Pocock's `prototype` skill (`skills/engineering/prototype`,
upstream `github.com/mattpocock/skills` at `4ae2317`, MIT, Copyright (c) 2026 Matt
Pocock). The licence text ships in this reference's `ATTRIBUTION` section.

## Pick the branch before writing anything

- **"Does this logic or state model feel right?"** -> [Logic](#logic-branch).
  A single shareable HTML file pushing the state machine through the cases that
  are hard to reason about on paper.
- **"What should this look like?"** -> [UI](#ui-branch). Several radically
  different variations on one route, switchable while the page runs.

The two produce very different artifacts, so getting this wrong wastes the whole
prototype. If the question is genuinely ambiguous, default to whichever branch
matches the surrounding code (a backend module -> logic; a page or component ->
UI) and **state that assumption at the top of the prototype** so it can be
corrected cheaply.

## Rules that apply to both branches

1. **Throwaway from day one, and named as such.** Put it close to where it would
   really live so context is obvious, but make the name say prototype. Obey the
   project's own routing and naming conventions; do not invent a new top-level
   structure.
2. **Trivial to run.** One command from the project's existing task runner, or a
   file you double-click. No setup thinking required.
3. **No persistence unless persistence is the question.** State lives in memory.
   If the question involves a database, hit a scratch database or a local file
   with an obvious throw-me-away name.
4. **No polish.** No tests, no error handling beyond what makes it runnable, no
   abstractions, no "what if we supported X later". A prototype that needs tests
   is not a prototype.
5. **Surface the state.** After every action, or on every variant switch, render
   the full relevant state so the change is visible.
6. **Capture the answer, then capture the prototype.** Fold the validated
   decision into the real code. Keep the prototype itself as a primary source:
   commit it to a throwaway branch off main and leave a pointer to that branch on
   the implementation issue or in the spec. Main keeps only the decision.

## Logic branch

Use this when the question is about business logic, state transitions or data
shape: the kind of thing that looks reasonable on paper and feels wrong the
moment it is pushed through real cases.

### 1. State the question visibly

One paragraph at the top of the demo, in a visible intro rather than a code
comment: the state model, and what is being asked of it. A prototype answering
the wrong question is pure waste, and the intro is what lets a later reader
(often the person who asked, returning later) check it.

### 2. Isolate the logic in a portable pure module

Put the logic that answers the question in one `<script>` block written as a
small pure module that could be lifted into the real codebase later. The page
around it is throwaway; this module is the part worth keeping.

Pick the shape that fits the question, not the one easiest to wire to a page:

- **A pure reducer**, `(state, action) => state`, when actions are discrete
  events and the state is one value.
- **An explicit state machine**, when "which actions are even legal right now"
  is part of the question.
- **A small set of pure functions** over a plain data type, when there is no
  implicit current state.
- **A class or module with a clear method surface**, when the logic genuinely
  owns ongoing internal state.

Keep it pure: no DOM, no `document`, no handlers reaching inside. The page calls
into it and nothing flows the other way. That purity is exactly what lets the
validated version lift into the real module afterwards.

### 3. Build the shareable file

One file, plain HTML/CSS/JS: no framework, no bundler, no server, everything
inline so it opens by double-click and survives being sent to someone. Write it
for a non-developer, in domain language rather than code, so a designer, a PM or
a domain expert can drive it. Lay it out top to bottom:

1. **Title and one line** naming the question this file explores.
2. **Current state**, rendered as a readable labelled panel rather than a raw
   JSON dump, re-rendered after every click, with what just changed called out
   where that helps.
3. **Free-play buttons**, one per action, always available, so anyone can poke
   the model in any order.
4. **Guided walkthroughs**, one tab per scenario: a plain-language description of
   the situation and what to watch for, then the ordered buttons to press, each
   a real button that performs the action and advances. Starting a walkthrough
   resets to a known initial state so it runs the same way every time.

Choose scenarios for the awkward cases: the happy path, a tricky edge case, and
an attempt at something that should be illegal. Restrained styling: clean
typography, generous spacing, one accent colour, nothing that competes with the
state and the buttons.

### 4. Hand it over and watch for the interesting moments

The interesting moments are "wait, that shouldn't be possible" and "huh, I
assumed X would be different". Those are bugs in the idea, which is the point.
Add actions or scenarios when asked; prototypes evolve.

### 5. Capture

The validated reducer, machine or function set lifts into the real module. The
HTML shell rides along to the throwaway branch, where being one self-contained
file makes it trivially re-runnable as a primary source.

### Logic anti-patterns

- Wiring it to the real database when persistence is not the question.
- Blurring logic and page: a "pure" module that references the DOM is no longer
  liftable.
- Shipping the HTML shell into production. The page is optimised for being
  clicked by hand; the module behind it is the part worth keeping.

## UI branch

Use this when the question is what something should look like.

### Two sub-shapes, and strongly prefer A

A variant is much easier to judge when it is butting up against the rest of the
app: real header, real sidebar, real data, real density. A throwaway route on its
own is a vacuum where every variant looks fine. Default to A whenever there is a
plausible existing page to host the variants.

**A. Variants inside an existing page (default).** Variants render on the same
route, gated by a `?variant=` URL search param. Existing data fetching, params
and auth all stay; only the rendering swaps. Something that has no page yet but
would naturally live inside one (a new dashboard section, a new settings card, a
new step in an existing flow) is still A: mount it inside the host page.

**B. A new page (last resort).** Only when the prototype genuinely has no nearby
home. Then create one route, clearly named as a prototype, and delete it when the
question is answered.

### Rules

- **Radically different, not variations on one idea.** Three near-identical
  layouts teach nothing. Differ in information hierarchy and density, not in
  border radius.
- **A floating bottom bar** naming each variant and switching the search param,
  so comparing is one click and the current one is always visible.
- **No persistence.** Variant choice is state in the URL, nothing more.
- **Capture.** The picked variant (or the bits stolen from several) is folded
  into the real page; the prototype route goes to the throwaway branch with the
  other branch's artifacts.

## ATTRIBUTION

Adapted from `github.com/mattpocock/skills` (`skills/engineering/prototype`,
SKILL.md, LOGIC.md, UI.md) at `4ae2317`, MIT licensed.

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
