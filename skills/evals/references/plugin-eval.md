# claude plugin eval

Claude Code's built-in eval runner (v2.1.269+). Each case runs a fresh `claude -p`
child with only the plugin loaded: no user settings, CLAUDE.md, other plugins or
project `.claude/`, and MCP servers are not started.

## Case layout

    evals/<case>/prompt.md        frontmatter + the prompt as the body
    evals/<case>/graders/*.md     one grader per file; the file stem is its name

`prompt.md` frontmatter: `name`, `tags: [a, b]`, `runs` (default 3), `max_turns`
(default 10), `timeout_seconds` (default 300), `allowed_tools: [Read, Glob, Grep, Skill]`.
Bash, Write, Edit, WebFetch and WebSearch are off unless granted with `--allow-tools`.

`scripts/new_case.py SLUG EXPECT "PROMPT"` writes all of this for you.

## Graders

Skill fired (positive):

    ---
    type: tool_used
    tool: Skill
    input_match: '"skill"\s*:\s*"(?:[\w-]+:)?build"'
    ---

Skill stayed silent: the same plus `min: 0` and `max: 0`. One positive grader for the
expected skill and a silent one for every other skill turns a suite into a confusion
matrix. Do not escape `-` in the skill name: `\-` breaks a unicode JS regex.

Reference read (depth): `tool: Read` with `input_match: 'references/supabase\.md'`, or
`max: 0` for must-not-read. It matches the Read ATTEMPT, so it proves the router
pointed at the file, not that the file says anything useful.

## Running

    claude plugin eval . --tag smoke --runs 2 --ablation none --trust-plugin \
      --no-publish --model claude-opus-5-5 --threshold 0 --max-cost-usd 10 --json r.json

- `--ablation none`: skip the no-plugin baseline arm (useless for trigger tests).
- `--tag T` (repeatable) / `--case GLOB`: select cases. `-j N`: run N at once (1-8).
- `--threshold X`: exit 1 if any case scores below X (default 1.0); 0 to only collect.
- `--max-cost-usd N`: hard ceiling; a partial run exits 2 and sets `"partial": true`.
- Exit codes: 0 pass, 1 below threshold or load error, 2 partial, 130/143 interrupted.
- Result JSON: `cases[].name`, `cases[].arms.with[]` (one per run) `.graders[].{name,passed,explanation}`, top-level `costUsd`.

## Cost and noise

- Measured: about $0.07 per agent run on the default model (one Skill call plus one
  Read). Cost is cases x runs; say the number before a paid pass.
- One run is noisy. Use 2-3 runs per case and judge only on the held-out split.
- A skill's NAME alone often routes the obvious prompts (a placeholder description
  still fired on "my API key is missing"). The hard cases are near-misses and
  phrasings that never use the name's words; write those deliberately.
