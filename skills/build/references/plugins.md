
# Pluginize

Goal: a teammate runs two commands (`claude plugin marketplace add <owner>/<repo>`, `claude plugin install <name>@<marketplace>`), answers the config prompts, restarts, and everything works. No copied folders, no shared tokens, no hand-edited JSON.

This file is the opinionated layer. For general plugin craft (manifest fields, skill and agent writing, hook events), also follow Anthropic's `plugin-dev` plugin skills if installed (`plugin-structure`, `skill-development`, `agent-development`, `hook-development`, `mcp-integration`, `plugin-settings`). Official reference: https://code.claude.com/docs/en/plugins/manifest-reference.md. A decision the repo documents wins over this file.

**Read `references/plugins-traps.md` before writing anything.**

## 1. Pick the mode, or stop

- **Mode A, package:** skills, agents, commands, hooks or MCP servers that more than one person should use, sitting loose in `~/.claude/`, symlinked from a repo, or in a repo without a manifest. Also: an existing plugin with problems (fix in place).
- **Mode B, plugin + service:** the plugin's MCP server or CLI needs a running backend someone may want their own copy of (e.g. a memory plugin whose users can run their own copy of the memory service). Mode B = mode A + the steps in section 5.

Stop and say so when:
- It is one personal skill only its author uses: leave it in `~/.claude/skills/`.
- A skill edits its own files as it learns (like `dockerize` with `traps.md`): plugin installs live in a cache that is overwritten on update, so the learning is lost. Ship it as a git repo cloned into `~/.claude/skills/<name>` instead. Or, as dev-skills does, have it record lessons as a PR to its source repo.
- The content is mostly secrets or one person's private config.

Give the verdict and mode in one or two lines, then proceed unless a stop condition applies. Mode B follows `references/containers.md`.

## 2. Inventory

List every component with file:line evidence:
- Skills (`SKILL.md`), agents (`agents/*.md`), commands (`commands/*.md`), hooks (`hooks.json` or `settings.json` hooks), MCP servers (`.mcp.json`, `settings.json`, `~/.claude.json`), output styles, LSP servers.
- Where each really lives. Resolve symlinks (`ls -la ~/.claude/skills`). The plugin is built in the repo that owns the source, never from the symlink target's copy.
- What each depends on: MCP tools it calls (`mcp__<server>__*`), CLIs it expects on PATH, env vars, other plugins, a backend URL.
- **Secrets.** Grep every file that will ship, case-insensitive: `grep -rniE '(token|secret|key|password)["'"'"' ]*[:=]|Bearer [A-Za-z0-9._-]{16,}|sk-[A-Za-z0-9]{16,}|ghp_|github_pat_|nco_|xox[bp]-|eyJ[A-Za-z0-9]{20,}' <dir> | cut -c1-120`, and git history: `git log -p --all | grep -niE '<same pattern>' | cut -c1-80`. Report the file and key name only, never the value. Each one becomes a `userConfig` entry (section 3). If a secret is already committed, tell the user it is in git history and needs rotating. Do not rotate it yourself.
- Name collisions: `find "${PLUGINIZE_SEARCH_ROOT:-$HOME}" \( -path '*/.claude-plugin/plugin.json' -o -path '*/.claude-plugin/marketplace.json' \) -not -path '*/node_modules/*' -not -path '*/.claude/worktrees/*' -exec sh -c 'printf "%s %s\n" "$(jq -r .name "$1")" "$1"' _ {} \; | sort` plus `claude plugin list` and `claude plugin marketplace list`. A repeated name is only a collision when the two paths belong to different repos (`git -C <dir> rev-parse --git-common-dir` differs; sibling worktrees share one). Two plugins with the same `name` shadow each other, and a second marketplace with the same `name` silently repoints the first.

Work in a git worktree off the owning repo's remote default branch, not local HEAD: `git fetch -q origin && D=$(git remote show origin | awk '/HEAD branch/{print $3}') && git worktree add ../<repo>-pluginize -b pluginize origin/$D` (no remote: use HEAD). Local HEAD can carry commits that were never pushed, and a PR from it would ship them too. Never touch the user's working tree. Defaults:
- Uncommitted or unpushed changes to the files being packaged: list them and ask whether to commit and push first; the branch would silently drop them.
- No owning repo (skills only in `~/.claude/`): create `~/<parent of other repos>/<name>` with `git init`, copy the components in, name = folder name.
- Never delete or move anything in `~/.claude/` yourself. As the last step, list the loose copies the plugin replaces (they would fire twice) and offer to remove them.

## 3. Write the plugin

Layout at the plugin root:
```
.claude-plugin/plugin.json
.claude-plugin/marketplace.json      # default: single-plugin marketplace in the same repo
skills/<skill>/SKILL.md
agents/*.md
commands/*.md
hooks/hooks.json
.mcp.json
INSTALL.md
```
If the repo also holds skills or commands that must not ship (operator-only), put the plugin in a subfolder (`plugin/`) with `marketplace.json` at the repo root and `"source": "./plugin"`. The manifest `skills` key only adds to the default `skills/` scan, so a plugin rooted at the repo root ships every skill in `skills/`.

**plugin.json**
```json
{
  "name": "acme-example",
  "version": "1.0.0",
  "description": "One sentence: what it gives you.",
  "author": { "name": "Acme" },
  "userConfig": {
    "api_token": { "type": "string", "title": "API token", "description": "Where to get it, in one line.", "required": true, "sensitive": true },
    "api_url":   { "type": "string", "title": "API URL", "description": "Leave the default unless told otherwise.", "default": "https://api.example.com" }
  },
  "dependencies": []
}
```
- `name`: kebab-case, default = the repo name, unique across the org (checked in step 2). `version`: semver, bumped on every release; users stay pinned until it changes.
- Every secret is a `userConfig` entry with `sensitive: true` (masked, stored in the OS secure store). Every URL a user might change is a `userConfig` entry with a default. Every entry needs `type`, `title` and `description` or strict validation fails.
- Another plugin this one needs goes in `dependencies` (`{"name": "x", "version": "^1.0"}`), not in the README.

**.mcp.json**
```json
{ "mcpServers": { "example": {
  "command": "node",
  "args": ["${CLAUDE_PLUGIN_ROOT}/server/server.mjs"],
  "env": { "API_URL": "${user_config.api_url}", "API_TOKEN": "${user_config.api_token}" }
} } }
```
- A remote HTTP MCP: `{ "type": "http", "url": "${user_config.api_url}", "headers": { "Authorization": "Bearer ${user_config.api_token}" } }`.
- Paths use `${CLAUDE_PLUGIN_ROOT}`. It changes on every update, so never store state there.
- State that must survive updates (caches, generated files, a compose project's `.env`) goes in `${CLAUDE_PLUGIN_DATA}`.
- Ship a prebuilt bundle (`server/*.mjs`) or a published package, not a source tree that needs `npm install` on the user's machine. A top-level `bin/` is put on the Bash tool's PATH and claude.ai/Cowork refuse plugins that have one: use `bin/` only for CLIs meant to be on PATH (an existing `bin/` in a shipped plugin is fine for Claude Code; say so in the report).
- Hook processes can also read `CLAUDE_PLUGIN_OPTION_<KEY>` env vars; MCP processes cannot (verified: none arrive), so pass MCP values through `env`. `${user_config.*}` is not allowed in shell-form hook commands: use exec form or the env var.
- An unset option resolves to its `default`, or to `""` without one (never the literal placeholder), so the server must treat an empty token as "not configured".

**Hooks**: keep `SessionStart` hooks under a second and never blocking: check, print one hint line, exit 0. Setup work belongs in a command the user runs once.

**marketplace.json** (single-plugin repo):
```json
{ "name": "acme-example", "description": "One line: what this marketplace offers.", "owner": { "name": "Acme" },
  "plugins": [ { "name": "acme-example", "source": "./", "description": "Same sentence as plugin.json." } ] }
```

**INSTALL.md**, for someone who has never edited JSON:
1. **What you get**, one sentence.
2. **Install**: `claude plugin marketplace add <owner>/<repo>`, `claude plugin install <name>@<marketplace>`. Private repos need `gh auth login` once.
3. **Configure**: what each `userConfig` prompt asks and where to get the value; `claude plugin configure <name>` to change it later.
4. **Restart Claude Code**, then one sentence to type that proves it works.
5. **Update**: `claude plugin update <name>@<marketplace>`, then restart.
6. **If something goes wrong**: the three most likely failures from this run and `references/plugins-traps.md`.

## 4. Verify (mandatory, in an isolated Claude config)

Never test by installing into the user's real config. Shell state does not persist between tool calls, so an `export` in one call is gone in the next: prefix **every** command with the throwaway dir, or run this block as one script.
```bash
D=$(mktemp -d); echo "$D"                        # throwaway config root; reuse this literal path in every later call
CLAUDE_CONFIG_DIR=$D claude plugin marketplace list    # must list nothing: proves isolation before anything is installed
claude plugin validate --strict <plugin-root>
claude plugin validate --strict <marketplace-root>   # if different: a path validates only one manifest
claude plugin validate --strict <plugin-root>/.claude-plugin/plugin.json   # when both manifests share one .claude-plugin/, the directory form checks only marketplace.json
git clone -q --depth 1 file://<worktree> "$D/src"      # committed files only, like GitHub (a local path runs in place and would hide gitignored or uncommitted files)
CLAUDE_CONFIG_DIR=$D claude plugin marketplace add "$D/src/<marketplace-root-relative>"
CLAUDE_CONFIG_DIR=$D claude plugin install <name>@<marketplace>
printf '%s' '{"api_url":"...","api_token":"test"}' | CLAUDE_CONFIG_DIR=$D claude plugin configure <name>@<marketplace> --values-stdin
CLAUDE_CONFIG_DIR=$D claude plugin list          # installed, enabled
CLAUDE_CONFIG_DIR=$D claude plugin details <name>@<marketplace>   # every component present; note the always-on token cost
```
Commit on the worktree branch before cloning. If any command above ran without the prefix, stop and tell the user what may have landed in the real config.
Then prove behavior:
- Each skill triggers: one `claude plugin eval` case per shipped skill (max 6; name the rest in the report). From the plugin root, `claude plugin eval init --bare <case>` scaffolds `evals/<case>/prompt.md` and `graders/criteria.md` (a paid LLM grader): replace it with `graders/fired.md` whose frontmatter is `type: tool_used`, `tool: Skill`, `input_match: '"skill"\s*:\s*"(?:[\w-]+:)?<skill>"'`. Add `evals/results/` to `.gitignore`. Run eval with the real login (a throwaway config has no login; see traps.md) against the path, which installs nothing: `claude plugin list --json > /tmp/before.json; claude plugin eval <plugin-root> --trust-plugin --runs 1 --ablation none --model haiku --no-publish; claude plugin list --json | diff /tmp/before.json -`. MCP servers are not started during eval, so a skill that goes on to call its MCP may time out after firing; the trigger grader still counts.
- Each MCP server starts and answers one read-only call. Use a real test token if the user provides one; otherwise prove the server starts and returns a clean auth error, and say so.
- A grep of `$D` (clone, cache and data) finds no secret values. `CLAUDE_CONFIG_DIR=$D claude mcp list` also starts each plugin MCP server: a quick "it starts" check. On Linux, sensitive values land in `$D/.credentials.json` (key `pluginSecrets.<name>@<marketplace>.<key>`); a test script can read the token from there into the server's env without printing it. On macOS they may go to the real login Keychain even with an isolated dir: use only a dummy token there, check Keychain Access afterwards, and record what you find in traps.md.
- Clean up: `rm -rf "$D"`.

If `CLAUDE_CONFIG_DIR` isolation does not work in this Claude Code version, record that in `references/plugins-traps.md` and stop before touching the real config. Ask the user.

## 5. Mode B: the service behind the plugin

1. The service must already be packaged per `references/containers.md`. If it isn't, do that first.
2. The plugin cannot build from the service's repo, so the compose file it ships must use **published images** (`image: ghcr.io/<owner>/<system>:<version>`, no `build:`). If images are not published yet, stop and say publishing comes first.
3. Ship the compose file inside the plugin (`service/compose.yaml`) with a fixed top-level `name:`, so volumes and data survive plugin updates even though `${CLAUDE_PLUGIN_ROOT}` moves. Replace relative bind mounts (`./backups:/backups`) with named volumes: `./` resolves inside the plugin cache, which an update replaces. Remove any service that echoes a generated secret to its logs. Tests override the fixed name with `COMPOSE_PROJECT_NAME` (it beats `name:`).
4. Add a `backend` userConfig option: `hosted` (company URL + your token) or `local` (your own copy).
5. Add a setup command (`commands/setup.md`) that runs one script (`node "${CLAUDE_PLUGIN_ROOT}/service/setup.mjs" $ARGUMENTS --data "${CLAUDE_PLUGIN_DATA}"`: node, not sh, so it works on Windows; a script, so it is testable without a session). `${CLAUDE_PLUGIN_*}` is substituted in the command body but is not in the Bash tool's env, so pass it as an argument. For `local` the script runs `docker compose -f <script dir>/compose.yaml up -d --wait`, gets the URL from `docker compose port`, reads the generated admin token from the container into a pipe, and saves URL + token with `claude plugin configure <name>@<marketplace> --values-stdin` (the bare name is rejected; find the id in `claude plugin list --json`), writing the JSON to stdin, never to argv or the terminal. Then it tells the user to restart. It must be safe to run twice. Persist choices like port in `${CLAUDE_PLUGIN_DATA}`, not next to the compose file.
6. Optional `SessionStart` hook for `local`: read `CLAUDE_PLUGIN_OPTION_<KEY>`, one fast health check (in node: `fetch(url + '/health', { signal: AbortSignal.timeout(1000) })`, no curl on Windows); if down, print "run /<name>:setup" and exit 0.
7. Verify both backends in the isolated config: `hosted` with a test token (or the clean auth error), and `local` end to end: setup command, health, one MCP read call returning data from the local service, second setup run is a no-op.

## 6. When verification fails: fix, then teach the skill

Same loop as `references/containers.md`, max 5 attempts per failure: read the real error, fix in the worktree, re-run section 4 from a fresh isolated config. Once green, generic causes go into `references/plugins-traps.md` (format in that file), or correct this file if an instruction was wrong. Never record a trap that was not reproduced and then verified fixed.

Share it with the "Recording a lesson" section of build's SKILL.md (a PR to this plugin's source repo; never edit the installed copy).

## 7. Report

- Verdict and mode.
- Components found, where they lived, and where they are now.
- Secrets found (file + key name only) and whether they are in git history.
- Worktree, branch, commit.
- Verification output: validate, list, details token cost, eval results, MCP call, secret grep.
- Traps added or skill lines changed.
- What only the user can do: rotate leaked secrets, push, merge, publish images, tag the release (`claude plugin tag --push`).
