# dev-skills

Three Claude Code skills for the parts of building that usually get skipped: stress-testing the plan, measuring whether a skill or prompt actually works, and packaging the result so someone else can install it.

| Skill | Fires on | Goes deeper into |
|---|---|---|
| `grill` | grill this plan, poke holes, stress-test this spec, what did I miss | `adversary-prompt.md` |
| `evals` | write evals, did this change make it better, does my skill fire, tune a skill description | `plugin-eval.md`, `mining.md`, `hillclimb.md` + 5 stdlib Python scripts |
| `build` | dockerize this, one-command setup, make this a plugin, package these skills | `containers.md`, `plugins.md`, plus a traps file for each |

Each skill is a short router. The reference files load only when the task needs them.

## Install

```bash
claude plugin marketplace add LeadGrowGTM/dev-skills
claude plugin install dev-skills@dev-skills
```

Restart Claude Code. The skills show up as `dev-skills:grill`, `dev-skills:evals` and `dev-skills:build`.

Optional tools: `grill` uses the `codex` CLI as the adversary when it is installed and falls back to a read-only subagent otherwise. `evals` needs Claude Code v2.1.269+ for `claude plugin eval`. `build` needs Docker for the container path.

## What each one does

**grill.** Takes a written plan and runs up to five unattended rounds: an adversary that cannot edit attacks the plan, and the agent settles every attack from source (file:line, a command, the docs) or changes the plan. Only questions that need a human (intent, priority, spend) come back, in one batch. It ends by appending a verdict with counts, plan changes and accepted risks.

**evals.** Covers `claude plugin eval` cases and graders, turning your own session logs into test cases (with scrubbing and a mandatory human review), and hill-climbing skill descriptions against a fixed 60/40 train/hold split. `scripts/new_case.py` writes one case with a must-fire grader for the expected skill and a must-stay-silent grader for every other skill, so a suite is a confusion matrix.

**build.** Two packaging playbooks. Containers: qualify the repo first (many should not be dockerized), then write a multi-stage Dockerfile, a compose file that generates its own secrets with no bash on the host, backups, an INSTALL.md for non-terminal users, and verify on a fresh clone including arm64. Plugins: inventory every component and secret, write the manifest with `userConfig` for secrets, and verify in a throwaway `CLAUDE_CONFIG_DIR` so nothing lands in your real config. Both carry a traps file of failures hit on real repos, each reproduced and verified fixed.

## How we know it works

`bash scripts/green.sh` runs the unit tests (case writer, log miner scrubbing, proposal validation, the tuning loop's keep/revert logic, the lint), the structure lint and `claude plugin validate`.

Trigger evals live in `evals/`: 9 cases, two positives per skill plus near-misses that should fire nothing (a diff review is not `grill`, unit tests are not `evals`, a Dockerfile error is not `build`). On 2026-10-21 with `claude-opus-5-5`, 2 runs each: **18/18 passed**, $1.75.

```bash
claude plugin eval . --runs 2 --ablation none --trust-plugin --no-publish \
  --model claude-opus-5-5 --threshold 0 --max-cost-usd 3 -j 4
```

The suite is small on purpose. Add cases from your own phrasing with `python3 skills/evals/scripts/new_case.py SLUG EXPECT "PROMPT"`.

## A skill never fires?

Too many skills installed. Claude Code fits all skill descriptions into a budget of about 1% of the context window and drops the least-used ones first, and a just-installed skill has never been used. Check with `/skill-doctor`: a skill listed by name only will rarely fire. Turn off plugins you never use, or raise the budget in `~/.claude/settings.json` with `"skillListingBudgetFraction": 0.03`.

## Contributing

- Edit a skill, then run `bash scripts/green.sh`.
- Changed a description? Re-run the trigger evals above before opening a PR.
- Hit a packaging failure the traps files don't cover? Add it to `skills/build/references/containers-traps.md` or `plugins-traps.md` in the format at the top of the file. Only record traps you reproduced and then verified fixed.
- Bump `version` in `.claude-plugin/plugin.json` on every behaviour change.

## License

MIT. See [LICENSE](LICENSE).
