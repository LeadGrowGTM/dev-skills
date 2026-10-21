---
name: train-build-fix-didnt-take
tags: [train, expect-build, smoke, depth]
runs: 3
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
---
I fixed the null check in my CLI's config loader but it still crashes exactly the same way. debug this
