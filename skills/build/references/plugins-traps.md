# Traps

Failures this skill has hit on real plugins. Read before writing anything. Append new entries at the bottom.

Format:
```
## <short symptom>
- Seen: <repo>, <YYYY-MM-DD>
- Symptom: <what the user or the test saw>
- Cause: <root cause>
- Fix: <what to write instead>
```

## Edits to an installed plugin vanish
- Seen: charlesdr-dev-loop, 2026-08-11
- Symptom: a fix made in the installed plugin is gone after the next update, or never loads.
- Cause: installs are copied into `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`; the cache is replaced on update and the version pins what loads.
- Fix: edit the source repo, bump `version`, reinstall or `claude plugin update`, restart. Persistent state goes in `${CLAUDE_PLUGIN_DATA}`.

## Two plugins share one name
- Seen: a forked plugin, 2026-09-30
- Symptom: the fork's `plugin.json` and `marketplace.json` both kept the upstream name, the same as the already-installed upstream plugin. Adding the second marketplace printed only "Plugins already installed from it now update from the new source": the existing infra-orchestrator marketplace was silently repointed at the fork.
- Cause: manifest copied from the upstream repo at fork time and never renamed. The marketplace `name` collides too, not just the plugin `name`.
- Fix: step 2's name-collision check covers both manifests; rename plugin and marketplace to the repo's own name and bump the major version (the command namespace changes). Verify by adding both marketplaces and installing both in one throwaway config: both list as enabled.

## Shared token committed in `.mcp.json`
- Seen: an MCP plugin with a local backend, 2026-09-30
- Symptom: `.mcp.json` sets `SERVICE_TOKEN` to a literal value, tracked in git since the first plugin commit.
- Cause: "one-click" install shipped one token to everyone instead of asking each user.
- Fix: `userConfig` entry with `sensitive: true`, referenced as `${user_config.<key>}` in `.mcp.json` env. Rotate the old token (owner's call). Also rewrite every doc or command that tells people to copy the token out of `.mcp.json`. Verified: the old value is in no file of the installed cache or plugin root; a dummy token gets a clean 401.

## Strict validate fails on the marketplace
- Seen: a remote-MCP plugin, 2026-09-30
- Symptom: `claude plugin validate --strict <repo-root>` fails with `description: No marketplace description provided`, while the plugin folder validates clean.
- Cause: `marketplace.json` has no top-level `description`; `--strict` turns that warning into an error. Validating the plugin folder alone never checks the marketplace file.
- Fix: add a top-level `"description"` to `marketplace.json` and validate both the marketplace root and the plugin root.

## Evals cannot run in the throwaway config
- Seen: a remote-MCP plugin, 2026-09-30
- Symptom: `claude plugin eval` in a fresh `CLAUDE_CONFIG_DIR` exits 2 with `Not logged in`.
- Cause: the throwaway config has no credential.
- Fix: run eval with the real login against the plugin path (`claude plugin eval <plugin-root> --trust-plugin ...`); it sandboxes and installs nothing. All 4 of the plugin's skills fired, $0.16. Do not copy the credentials file.

## Strict validate fails on the plugin root with `CLAUDE.md`
- Seen: a forked plugin, 2026-09-30
- Symptom: `claude plugin validate --strict <repo-root>` fails with `root: CLAUDE.md at the plugin root is not loaded as project context`.
- Cause: the plugin is rooted at the repo root, so the whole repo (CLAUDE.md, app code, docs) is the plugin and is copied into the cache.
- Fix: move the plugin into `plugin/` (`git mv` the commands/skills there, marketplace `"source": "./plugin"`). If the repo also uses those commands as project commands, leave a symlink at the old `.claude/commands/<dir>` pointing at `../../plugin/commands`. The cache dropped to 22 files and both roots validated strict.
- Lighter fix when the repo must stay the plugin root (e.g. a release script writes into `bin/`): `git mv CLAUDE.md .claude/CLAUDE.md`. Claude Code still loads it as project memory and strict validate passes.

## Empty value does not clear a sensitive option
- Seen: an MCP plugin with a local backend, 2026-09-30
- Symptom: `printf '{"token":""}' | claude plugin configure <id> --values-stdin` prints `No configuration changes`; the old secret stays and keeps reaching the MCP server.
- Cause: `--values-stdin` ignores empty strings for a set sensitive option.
- Fix: never design a flow that relies on clearing a secret (e.g. "switch backend = wipe token"). Overwrite it with the new value, or tell the user to paste theirs. Verified: the setup script's `hosted` path now only switches backend + URL and asks for the token.

## Plugin `bin/` CLI loses to an older copy on PATH
- Seen: a CLI plugin, 2026-09-30
- Symptom: after installing the plugin, `wiki` in a session still ran the old `~/.local/bin/wiki` symlink from the pre-plugin `install.sh`. `type -a wiki` listed the plugin's `bin/wiki` last.
- Cause: Claude Code appends the plugin's `bin/` to the end of the Bash tool's PATH, so any same-named command already on PATH wins.
- Fix: when a CLI moves into a plugin `bin/`, list the old PATH copy with the loose skill copies to remove, and add `type -a <cli>` to INSTALL.md troubleshooting. Verified: with `~/.local/bin` off PATH, `type -a wiki` in a `--plugin-dir` session resolves to the plugin's `bin/wiki`.

## PR carries someone's unpushed commits
- Seen: a remote-MCP plugin, 2026-09-30 (same bug hit a dockerize run)
- Symptom: the pluginize branch held 1 local commit that was never pushed; a PR would have shipped it.
- Cause: the worktree branched from local HEAD.
- Fix: branch from `origin/<default>` after `git fetch` (step 2). Rebuilt by cherry-picking only the plugin commit onto origin/main.

## Plugin MCP server hidden by a manual server of the same name
- Seen: a remote-MCP plugin, 2026-09-30 (swapping a real user from manual MCP to the plugin)
- Symptom: after install + configure, `claude mcp list` still showed only the old user-scope server of the same name; the plugin's server was not listed, and `claude plugin configure --json` shows a sensitive value as `""`, so there was no way to tell whether the token was saved.
- Cause: a user-scope MCP server with the same name shadows the plugin's server.
- Fix: back up `~/.claude.json`, pipe the old token into `claude plugin configure <id> --values-stdin` (never print it), then `claude mcp remove <name> -s user`; `claude mcp list` then shows `plugin:<plugin>:<server> ... Connected`, which proves the token works. INSTALL.md must tell users to remove the manual server.
