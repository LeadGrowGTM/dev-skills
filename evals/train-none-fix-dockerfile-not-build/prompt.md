---
name: train-none-fix-dockerfile-not-build
tags: [train, expect-none]
runs: 3
max_turns: 4
allowed_tools: [Read, Glob, Grep, Skill]
---
my Dockerfile build fails with EACCES on npm ci, why?
