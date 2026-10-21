---
name: build
description: Package a project so other people can install it in one step. Use when the user says dockerize this, make this installable, one-command setup, docker compose for this repo, make it run on Windows and Mac, or wants skills, hooks, agents, commands or MCP servers turned into a Claude Code plugin (pluginize this, make this a plugin, package these skills, share my skills with the team). Qualifies the project first and says when a lighter path is better, then writes the files and verifies them on a clean copy before claiming success.
---

# build

Pick the job, read its reference before writing anything, then follow it.

| Task | Read first |
|---|---|
| Package a repo as a Docker one-command install | `references/containers.md` |
| Package skills/hooks/agents/MCP into a Claude Code plugin | `references/plugins.md` |

A plugin whose MCP server needs its own backend reads both.

## Rules for both

- Secrets never go in a committed file, a command line, or the transcript.
- Do not deploy, push, or open a PR until the user asks. "Build it" is not "ship it".
- Work in a git worktree off the remote's default branch for anything that will become a PR.

## Recording a lesson

Each reference has a traps file (`references/containers-traps.md`,
`references/plugins-traps.md`). When a fix generalises to other repos, record it
there as a PR to this plugin's source repo. Never edit this installed copy: the
plugin cache is overwritten on update. Ask the user before pushing.
