# Mining session logs into eval cases

`<evals>` is the evals skill directory (the parent of this `references/` folder). Run the commands from the root of the plugin you are evaluating; `--plugin` defaults to the current directory.

Real phrasing beats invented phrasing, but logs are noisy and private. The pipeline:

1. **Map** old and new skill names to the skill that should fire, in a JSON file:
   `{"map": {"<skill name>": "<skill or none>"}, "none": "<what belongs elsewhere>"}`.
   Include neighbouring skills mapped to `none`; they become near-miss cases.
2. **Mine**: `python3 <evals>/scripts/mine.py --map <map.json> [--plugin DIR] [--logs ~/.claude/projects]`.
   For each Skill call it keeps the session's opening prompt plus the 3 user turns
   before the call, because the line right before a call is often just "go" or
   "do recom". Output: `<plugin>/evals/mine-out/candidates.jsonl` (gitignore it).
3. **Scrub** happens in mine.py: emails, key-shaped strings and home paths are
   replaced; pasted chat is kept but cut to 400 chars, since it is often the intent
   itself. It CANNOT catch client or person names, so step 5 is mandatory.
4. **Propose**: `python3 <evals>/scripts/propose.py --map <map.json>` labels each candidate
   with `claude -p` (rewriting it as a standalone prompt, dropping unclear ones),
   then pads each skill to `--target` (default 40) with paraphrases and near-misses.
   Output: `evals/mine-out/proposed.jsonl`. Costs a few dollars at most.
5. **Human review**: `jq -r '[.expect,.source,.prompt]|@tsv' evals/mine-out/proposed.jsonl`.
   Delete or fix lines with real names, wrong labels or duplicates.
6. **Write cases**: `python3 <evals>/scripts/make_cases.py`. It tags the first 4 cases per
   (expect, split) as `smoke`. Then grep `evals/` for emails, keys and `/home/`
   before committing.

Codex sessions (`~/.codex/sessions`) are mostly machine-run lanes; mine.py reads
Claude Code logs only.
