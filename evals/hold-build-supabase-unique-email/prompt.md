---
name: hold-build-supabase-unique-email
tags: [hold, expect-build, smoke, depth]
runs: 3
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
---
add a unique constraint on email to our 2M-row users table in Supabase
