# Traps

Failures this skill has hit on real repos, each reproduced and then verified fixed. Read before writing files. Append new entries at the bottom.

Format:
```
## <short symptom>
- Seen: <repo>, <YYYY-MM-DD>
- Symptom: <what the user or the test saw>
- Cause: <root cause>
- Fix: <what to write instead>
```

## Private CLIs install as stubs, stack still reports healthy
- Seen: a Node agent runtime with private CLIs, 2026-07-23; cause corrected 2026-09-30 (tested on Compose 2.40.3)
- Symptom: build exits 0, `/health` 200, every private CLI prints "not installed" and exits 1.
- Cause: the compose file declared no build secret, so `--mount=type=secret,id=gh_token` got nothing and the install step fell back to a stub. (The earlier note that compose cannot pass build secrets was wrong.)
- Fix: `build: { context: ., secrets: [gh_token] }` plus top-level `secrets: { gh_token: { environment: GH_TOKEN } }`, run with `GH_TOKEN=$(gh auth token)`. Fail the build when the secret is empty (`test -s /run/secrets/gh_token || exit 1`).

## Every API call returns 401 after `.env` edited on Windows
- Seen: a Node agent runtime with private CLIs, 2026-07
- Symptom: tokens look right, every authenticated call fails.
- Cause: CRLF line endings leave `\r` on each value.
- Fix: `.gitattributes` with `* text=auto eol=lf`; prefer generated secrets in the `app-secrets` volume over `.env` values.

## Quoted value in `.env` breaks the connection string
- Seen: a wiki app, 2026-07
- Symptom: Postgres fails with `host=base`.
- Cause: `docker run --env-file` keeps quotes literally.
- Fix: values unquoted in `.env` and `.env.example`.

## Changed `.env`, restart, nothing changes
- Seen: a wiki app, 2026-07
- Cause: `docker restart` does not re-read env.
- Fix: `docker compose up -d` recreates changed containers.

## Updated file ignored after deploy
- Seen: a Node + Postgres app, 2026-08
- Cause: a single-file bind mount pins the old inode when the file is replaced.
- Fix: bake the file into the image, or mount its directory.

## Copy of the engine never updates
- Seen: a Node + Postgres app, 2026-09
- Cause: compose mounted a prebuilt `dist/` into a generic `node:20-slim` container, so each install was a frozen copy.
- Fix: build the app into its own image, publish it, and update with `docker compose pull && docker compose up -d`.

## Ollama image eats 5 GB of disk for a CPU embedder
- Seen: a Node + Postgres + Ollama app, 2026-09-30
- Symptom: first `up` pulls `ollama/ollama` and the build then fails with `no space left on device`.
- Cause: `ollama/ollama` unpacks to ~5.4 GB of CUDA/ROCm libraries, even when only a CPU embedding model runs.
- Fix: `alpine/ollama:<tag>` (CPU-only, ~130 MB, amd64+arm64, same `ollama` entrypoint). SKILL.md Ollama snippet changed to it.

## `image ... already exists` when several services build one tag
- Seen: a Node + Postgres + Ollama app, 2026-09-30
- Symptom: `up --build` fails with `target <svc>: failed to solve: image "docker.io/library/<tag>": already exists` (containerd image store).
- Cause: every service with `build:` and the same `image:` builds in parallel and races to name the tag.
- Fix: `build:` on one service only; the others just reference `image:`. Compose builds it before starting them. SKILL.md compose snippet corrected (it had `build:` on both `migrate` and `app`).

## arm64 check fails with `exec format error`
- Seen: a Node + Postgres + Ollama app, 2026-09-30
- Symptom: `docker buildx build --platform linux/arm64` stops at the first `RUN` with `exec /bin/sh: exec format error`.
- Cause: no QEMU binfmt handler registered on the host, so arm64 `RUN` steps cannot execute.
- Fix: when build output is arch-independent, `FROM --platform=$BUILDPLATFORM ... AS build` and no `RUN` in the final stage. arm64 then builds natively in seconds. Added to SKILL.md Dockerfile section.

## Test cleanup `rm -rf` fails with Permission denied
- Seen: a Node + Postgres + Ollama app, 2026-09-30
- Cause: the backup container writes `./backups/*.sql.gz` as root through the bind mount (Linux hosts).
- Fix: delete through a container: `docker run --rm -v "$tmp:/t" alpine:3.20 rm -rf /t/app`. SKILL.md step 4 cleanup line changed.

## New `compose.yaml` hijacks the existing prod `docker-compose.yml`
- Seen: a Node + Postgres app, 2026-09-30 (avoided; reproduced in a scratch dir)
- Cause: with both files in one folder, compose warns `Found multiple config files` and uses `compose.yaml`, so the prod `docker compose up -d` would start the new stack.
- Fix: put the new stack in a subfolder (`standalone/compose.yaml` with `build: { context: .. }`). Added to SKILL.md compose rules.

## Next.js dashboard on hosted Supabase looked like a candidate
- Seen: a Next.js dashboard, 2026-09-30
- Symptom: runs continuously, so it seemed to qualify.
- Cause: its only "dependencies" were hosted Supabase and third-party API keys, it has one shared instance, and teammates already run it with `npm run dev`.
- Fix: step 1 now says a hosted service reached only with a key does not count as a dependency. Verdict: hand out the URL.

## Worker on the API image is unhealthy forever, `up --wait` fails
- Seen: a Python API + worker app, 2026-09-30
- Symptom: `api` healthy, `worker` (same image, other command) `unhealthy`; its health log is `curl: (7) Failed to connect to localhost port 8770`.
- Cause: the worker inherits the image's `HEALTHCHECK`, which curls the API port it never opens. `healthcheck: { disable: true }` is no way out: `up --wait` then fails with `container ... has no healthcheck configured` (compose 2.40).
- Fix: give the worker its own real `healthcheck:` in compose, e.g. a Python one-liner that connects to the database and selects from the queue table it drains.

## Template wants a local db, the repo documents a managed one
- Seen: a Python API + worker app, 2026-09-30
- Symptom: the compose template adds `db`, `migrate`, `backup` and `secrets-init`; the repo's compose says on purpose there is no database and `DATABASE_URL` points at managed Postgres.
- Cause: the schema is provider-specific (a throwaway Postgres refused the migrations: `supabase_vault is not installed`, `no role 'app_api'`), and its migrations are operator steps against a shared database.
- Fix: the documented decision wins. `DATABASE_URL` is an external key, no `db`/`migrate`/`backup`; test against a throwaway Postgres added only in an untracked override file (`-f docker-compose.yml -f ../test-override.yaml`). SKILL.md step 2 now says so.

## arm64 and Windows cannot be proven on the dev box
- Seen: a Node + Postgres app, 2026-09-30
- Fix: `verify-matrix.yml` (SKILL.md step 4). Real arm64 run passed in ~75 s; Windows Docker Desktop stays a human check.

## Private-repo token printed in the build log
- Seen: a Python API + worker app, 2026-09-30
- Symptom: plain build output shows the fetch step as `RUN set -eu; [ -n "gho_..." ]`, the real token.
- Cause: BuildKit expands `ARG` values in the step name it prints, so a literal `$TOKEN` or `${TOKEN:-}` in a `RUN` line lands in every build log, CI logs included. A separate fetch stage keeps it out of the final image, not out of the log.
- Fix: prefer a build secret (first trap above). Where the builder only passes ARGs (Railway), read it indirectly inside the shell: `"$(printenv TOKEN)"`. Verified: token occurrences in the `--progress plain` log went from 2 to 0 (`grep -c -F -f <tokenfile>`).

## PR carries someone's unpushed commits
- Seen: a Node + Postgres app, 2026-09-30 (and a plugin repo, same bug)
- Symptom: the PR showed conflicts in files the skill never touched (identity.ts, writeHandler.ts); merging would have shipped 8 unrelated local commits.
- Cause: the worktree branched from local HEAD, which was 8 commits ahead of origin/main.
- Fix: branch from `origin/<default>` after `git fetch` (step 2). Rebuilt by cherry-picking only the packaging commits onto origin/main; PR then showed 13 files, all ours.
