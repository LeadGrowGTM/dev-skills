# Contributing

Issues and PRs are welcome. Bug reports about a skill that did not fire, fired on the wrong ask, or gave advice that broke something are the most useful kind; include the exact prompt.

- Edit a skill, then run `bash scripts/green.sh`.
- Changed a description? Re-run the trigger evals in the README ("How we know it works") before opening a PR.
- Hit a packaging failure the traps files don't cover? Add it to `skills/build/references/containers-traps.md` or `plugins-traps.md` in the format at the top of the file. Only record traps you reproduced and then verified fixed.
- Bump `version` in `.claude-plugin/plugin.json` on every behaviour change.
- Keep each PR to one change, and say in it which check you ran and what it printed.

By taking part you agree to the [code of conduct](CODE_OF_CONDUCT.md).
