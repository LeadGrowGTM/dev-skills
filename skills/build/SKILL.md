---
name: build
description: Build features test-first and package projects so other people can install them. Use when the user wants to build a feature or fix a bug test-first, says tdd, red-green, write the failing test first, or make sure the tests really pass, or says dockerize this, make this installable, one-command setup, docker compose for this repo, make it run on Windows and Mac, or wants skills, hooks, agents, commands or MCP servers turned into a Claude Code plugin (pluginize this, make this a plugin, package these skills, share my skills with the team). Writes the check before the code, and verifies on a clean copy before claiming success.
---

# build

Pick the job, read its reference before writing anything, then follow it.

| Task | Read first |
|---|---|
| Build a feature or fix a bug test-first | `references/tdd.md` |
| Package a repo as a Docker one-command install | `references/containers.md` |
| Package skills/hooks/agents/MCP into a Claude Code plugin | `references/plugins.md` |

Work that spans two rows reads both (a plugin whose MCP server needs its own
backend; a Dockerfile change that needs a regression test).

## Rules for every row

- Nothing is done until its check ran and you have the output. "Should work" is not a result.
- Secrets never go in a committed file, a command line, or the transcript.
- Do not deploy, push, or open a PR until the user asks. "Build it" is not "ship it".
- Work in a git worktree off the remote's default branch for anything that will become a PR.

## Recording a lesson

The packaging references each have a traps file (`references/containers-traps.md`,
`references/plugins-traps.md`). When a fix generalises to other repos, record it
there as a PR to this plugin's source repo. Never edit this installed copy: the
plugin cache is overwritten on update. Ask the user before pushing.
