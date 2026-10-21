---
name: hold-build-bug-failing-test-first
tags: [hold, expect-build, smoke, depth]
runs: 3
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
---
users get charged twice when they double-click pay. fix it, but write a failing test that reproduces it first
