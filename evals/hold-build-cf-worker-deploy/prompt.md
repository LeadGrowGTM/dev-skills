---
name: hold-build-cf-worker-deploy
tags: [hold, expect-build, smoke, depth]
runs: 3
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
---
deploy my Cloudflare Worker to production and set its STRIPE_KEY secret
