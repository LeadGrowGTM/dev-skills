
# Dockerize

Goal: a person with only Docker Desktop runs `docker compose up -d` (no bash, no git, no hand-written secrets) and gets a working system, on Windows, Mac (Apple Silicon) and Linux.

This file is the opinionated layer. For generic Dockerfile and Compose craft (caching, non-root, pinned tags, secret mounts, loopback ports), also follow Docker's official skills if installed (`docker-project-foundations`, `docker-build-strategies`, `docker-compose-patterns`, `docker-destructive-guardrails` from github.com/docker/skills). Where they conflict with this file, this file wins.

**Read `references/containers-traps.md` before writing anything.** It holds every failure this skill has hit on real repos and the fix that worked.

## 1. Qualify first

Dockerize only if at least two are true:
- It runs continuously (API, worker, dashboard, DB-backed app).
- It needs more than one runtime or system dependency (Postgres, Redis, Ollama, native libs).
  A hosted service reached only with a key (hosted Supabase, Firebase, third-party APIs) does not count.
- Someone needs their own separate copy with their own data.
- It must run identically on Windows, Mac and Linux.

Stop and recommend the lighter path when it is: a Claude Code plugin or skill (already installable), a single CLI (`npm i -g`, `pip install`, one-line installer), a hosted service people only consume (hand out URL + key), or something needing a logged-in browser, GUI or host hardware (keep native). Give the verdict and reason in one or two lines before writing anything.

## 2. Read the repo

Find, with file:line evidence:
- Runtime and version (`package.json` engines, `.nvmrc`, `.python-version`, `pyproject.toml`, lockfile type).
- Build command, start command, and any migration or seed command.
- Every port and the health route. If none exists, add a minimal `/health` and say so.
- Every env var the code reads (grep `process.env`, `import.meta.env`, `os.environ`, `getenv`, `Settings(` classes). Classify each: **secret** (generate), **dependency URL** (point at a compose service), **external key** (user must supply, e.g. a third-party API key), **setting** (default it).
- Every external service it talks to, and which of those can run as a compose service.
- Private dependencies (`github:` / git URLs in lockfiles, private registries).

Work in a git worktree off the remote's default branch, not local HEAD: `git fetch -q origin && D=$(git remote show origin | awk '/HEAD branch/{print $3}') && git worktree add ../<repo>-dockerize -b dockerize origin/$D` (no remote: use HEAD). Local HEAD can carry commits that were never pushed, and a PR from it would ship them too. If a `dockerize` branch already exists, reuse it: `git worktree add ../<repo>-dockerize dockerize`. Never touch the user's working tree. If the local branch is ahead of origin or has uncommitted changes, tell the user they are not included. Reuse and fix existing Docker files rather than starting over. A decision the repo documents (a compose comment, the README) wins over this file's template: a managed database stays external, its URL is an **external key**, and there is no `db`/`migrate`/`backup` service. If the existing files already cover the goal, the verdict is "already packaged, these gaps".

## 3. Write the files

### Dockerfile
- `# syntax=docker/dockerfile:1` first line. Multi-stage: `build` stage with full tooling, final stage on a pinned slim base holding only runtime output and production deps.
- If the build output is architecture-independent (bundled JS, Go with `GOARCH`), start the build stage with `FROM --platform=$BUILDPLATFORM` and keep `RUN` out of the final stage. arm64 then builds without QEMU.
- Copy lockfile and install deps before copying source. Non-root user. Exec-form `CMD`/`ENTRYPOINT`. `EXPOSE` the port.
- Private deps: `RUN --mount=type=secret,id=gh_token ...` and fail the build loudly if the token is missing (`test -s /run/secrets/gh_token || exit 1`). Never let a missing token produce a stub that exits 0. Compose passes it with `build: { context: ., secrets: [gh_token] }` plus top-level `secrets: { gh_token: { environment: GH_TOKEN } }`, run as `GH_TOKEN=$(gh auth token) docker compose up --build`.
- Copy `docker-entrypoint.sh` (below) and use it as `ENTRYPOINT`.
- `.dockerignore`: `.git`, `node_modules`, `.venv`, `.env*` (but keep `.env.example`), build output, test data.

### docker-entrypoint.sh (secrets without bash on the host)
Loads generated secret files into env vars, so the app needs no code change:
```sh
#!/bin/sh
set -e
if [ -d /run/app-secrets ]; then
  for f in /run/app-secrets/*; do
    [ -f "$f" ] || continue
    name=$(basename "$f")
    eval "[ -n \"\${$name:-}\" ]" || export "$name=$(cat "$f")"
  done
fi
exec "$@"
```
An env var the user set explicitly wins over the generated file.

### compose.yaml
Everything needed to start comes from compose itself. No `.env` required.

```yaml
services:
  secrets-init:            # one-shot: generates missing secrets once, keeps them forever
    image: alpine:3.20
    command:
      - sh
      - -c
      - |
        for n in POSTGRES_PASSWORD APP_ADMIN_TOKEN; do
          [ -s /s/$$n ] || head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n' > /s/$$n
        done
        chmod 444 /s/*
        echo "admin token: $$(cat /s/APP_ADMIN_TOKEN)"
    volumes: [app-secrets:/s]

  db:
    image: pgvector/pgvector:pg16           # pinned; plain postgres:16-alpine if no vectors
    environment:
      POSTGRES_USER: app
      POSTGRES_DB: app
      POSTGRES_PASSWORD_FILE: /run/app-secrets/POSTGRES_PASSWORD
    volumes: [db-data:/var/lib/postgresql/data, app-secrets:/run/app-secrets:ro]
    depends_on: { secrets-init: { condition: service_completed_successfully } }
    healthcheck: { test: ["CMD-SHELL", "pg_isready -U app -d app"], interval: 5s, timeout: 3s, retries: 10, start_period: 10s }
    restart: unless-stopped

  migrate:                 # one-shot: schema/migrations, reruns safely on every up
    image: ${APP_IMAGE:-ghcr.io/<owner>/<repo>:latest}    # no build: here, only `app` builds the shared tag
    command: ["npm", "run", "migrate"]
    environment: { DATABASE_HOST: db }
    volumes: [app-secrets:/run/app-secrets:ro]
    depends_on: { db: { condition: service_healthy } }

  app:
    image: ${APP_IMAGE:-ghcr.io/<owner>/<repo>:latest}   # installers pull this; developers add --build
    build: .
    ports: ["127.0.0.1:${APP_PORT:-3000}:3000"]
    environment: { DATABASE_HOST: db }
    volumes: [app-secrets:/run/app-secrets:ro]
    depends_on: { migrate: { condition: service_completed_successfully } }
    healthcheck: { test: ["CMD", "node", "-e", "fetch('http://localhost:3000/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"], interval: 10s, timeout: 3s, retries: 5, start_period: 20s }
    restart: unless-stopped

volumes: { db-data: {}, app-secrets: {} }
```
Rules:
- The template is a Node + Postgres example. Drop `db`/`migrate`/`backup` if the app has no server database (SQLite goes in a named volume), drop `APP_ADMIN_TOKEN` if the app has no auth, and swap `npm`/`node` for the repo's runtime.
- The compose file must start with no source present: the default `image:` is the published ghcr tag, so someone who downloads only `compose.yaml` pulls instead of building. `build:` is for developers (`docker compose up -d --build`).
- Exactly one service gets `build:` per image tag. Two services building the same tag fail with `image ... already exists`.
- If the repo already has a `docker-compose.yml` that must stay, put the new file in a subfolder (`standalone/compose.yaml`, `build: { context: .. }`). A `compose.yaml` next to it silently wins.
- `$$` escapes `$` inside compose command strings. Forgetting it makes compose interpolate the value as empty.
- If the app wants a single `DATABASE_URL`, build it in the entrypoint from the secret, or teach the app to read `DATABASE_URL_FILE`. Do not put the password in compose.
- Settings get defaults: `${APP_PORT:-3000}`. Only **external keys** use `${VAR:?set VAR in .env}`, and only if the app cannot start without them. Prefer starting without them and failing that feature gracefully.
- Ports bind to `127.0.0.1` unless the user asked for LAN or internet exposure. Databases publish no host port.
- Named volumes for all data. No bind mounts of app code or single files. Named volumes also avoid slow and broken bind mounts on Windows and macOS.
- Healthcheck must hit something real, not a route that returns 200 while tools are missing.

### Ollama (only if the app embeds or generates locally)
```yaml
  ollama:
    image: alpine/ollama:0.34.4             # CPU-only, ~130 MB; pin, check the current tag
    volumes: [ollama-models:/root/.ollama]
    healthcheck: { test: ["CMD", "ollama", "list"], interval: 5s, timeout: 3s, retries: 20 }
  ollama-pull:                              # one-shot model download, shows progress in logs
    image: alpine/ollama:0.34.4
    environment: { OLLAMA_HOST: "ollama:11434" }
    entrypoint: ["ollama", "pull", "nomic-embed-text"]
    depends_on: { ollama: { condition: service_healthy } }
```
- Add `ollama-models: {}` to the top-level `volumes:`, or compose refuses the file.
- `ollama/ollama` unpacks to ~5.4 GB of CUDA/ROCm libraries. For embeddings (CPU is fine) use `alpine/ollama`. Use `ollama/ollama` only when the user has an NVIDIA/AMD GPU and a generation model.
- App reads `EMBED_URL` defaulting to `http://ollama:11434`, and `depends_on: ollama-pull: condition: service_completed_successfully`.
- Tell the user the first start downloads the model (hundreds of MB, several minutes) and to watch `docker compose logs -f ollama-pull`.
- Docker on Mac has no Apple GPU access, so Ollama in Docker runs on CPU there. Embedding models are fine on CPU. For heavy generation models, document `EMBED_URL=http://host.docker.internal:11434` with `extra_hosts: ["host.docker.internal:host-gateway"]` to use Ollama installed natively.

### Backups (any service with a database the user cares about)
```yaml
  backup:
    image: pgvector/pgvector:pg16           # same image as db, so pg_dump versions match
    environment: { PGHOST: db, PGUSER: app, PGDATABASE: app }
    entrypoint: ["sh", "-c", "export PGPASSWORD=$$(cat /run/app-secrets/POSTGRES_PASSWORD); while true; do pg_dump | gzip > /backups/app-$$(date +%F).sql.gz; find /backups -name '*.sql.gz' -mtime +7 -delete; sleep 86400; done"]
    volumes: [app-secrets:/run/app-secrets:ro, ./backups:/backups]
    depends_on: { db: { condition: service_healthy } }
    restart: unless-stopped
```
The `./backups` bind mount is deliberate: the user must be able to see and copy the files. Restore (works in PowerShell too, no gunzip on the host): `docker compose cp backups/app-DATE.sql.gz db:/tmp/restore.sql.gz` then `docker compose exec -T db sh -c "gunzip -c /tmp/restore.sql.gz | psql -q -U app app"`.

### Also write
- `.env.example`: every setting and external key, one comment each, no values for keys, no quotes.
- `.gitattributes`: `* text=auto eol=lf` so shell scripts and env files keep LF on Windows checkouts.
- `INSTALL.md` next to the compose file, written for someone who has never used a terminal. Sections, in order:
  1. **What you get**: one sentence, plus what it costs in disk and time on first start.
  2. **Before you start**: Docker Desktop (links for Windows and Mac), started and showing "running"; GitHub access if the repo or images are private (`gh auth login`, or `docker login ghcr.io`).
  3. **Install**: numbered copy-paste commands. Where Windows and Mac differ, show both (PowerShell and Terminal). Never assume bash on Windows.
  4. **Check it works**: the URL to open, what a good response looks like, how to get the admin token.
  5. **Connect it**: how to point Claude, a CLI or a browser at it, with the exact setting names.
  6. **Everyday**: update, stop, start, back up, restore, uninstall (and which command deletes data).
  7. **If something goes wrong**: the three most likely failures from this run and `references/containers-traps.md` (port in use, Docker not running, first start still downloading), each as symptom then fix, plus `docker compose logs <service>`.
  Link it from the repo README's "Get it running" section instead of duplicating it. Every command in it was run at least once this session (step 4, or by hand in the test clone); mark any that were not.
- `.github/workflows/publish.yml` from `assets/publish.yml` in the build skill directory: multi-arch (`linux/amd64,linux/arm64`) image to ghcr.io on tag push. Private org images need `docker login ghcr.io` with a PAT scoped `read:packages`. Say so in the README.

## 4. Verify on a clean copy (mandatory)

Do not claim success from reading files. From the worktree, after committing the new files on the `dockerize` branch:
```bash
P=dz-test-$(date +%s); export APP_IMAGE=$P:local APP_PORT=0   # own image tag and a free port: never overwrite or collide with someone else's
tmp=$(mktemp -d) && git clone -q --branch dockerize . "$tmp/app" && cd "$tmp/app"   # copy any stub .env for external keys in here now: the clone has none
docker compose -p $P up -d --build --wait --wait-timeout 600   # every service healthy or completed
docker compose -p $P ps -a                                     # one-shots exited 0
curl -fsS http://$(docker compose -p $P port app 3000)/health  # real response
docker compose -p $P logs secrets-init | tail -2               # token printed
docker compose -p $P restart && docker compose -p $P up -d --wait   # second start: same secrets, data kept
docker compose -p $P exec -T app sh -c 'id -u'                 # non-root (not 0)
docker buildx build --platform linux/arm64 -t dz-arm-check . && docker image rm dz-arm-check   # arm64 builds (needs QEMU unless the build stage uses $BUILDPLATFORM; skip only if disk or time is short, and say so)
docker compose -p $P down -v --rmi local && docker run --rm -v "$tmp:/t" alpine:3.20 rm -rf /t/app && rm -rf "$tmp"   # always clean up (backups/ is root-owned on Linux)
```
Then prove the platforms this machine cannot: copy `assets/verify-matrix.yml` from the build skill directory into the repo's `.github/workflows/`, replace every `<placeholder>` in it, push the branch (ask first) and watch it with `gh run watch`. It runs the same checks on `ubuntu-latest` and `ubuntu-24.04-arm` (real arm64, what Apple Silicon Macs run) and checks a Windows checkout keeps LF and the compose file parses. GitHub's Windows runners only run Windows containers, so Docker Desktop on Windows still needs one human run; say so in the report.

Pass = all of the above green. Anything the user must supply (external keys) is either stubbed in a `.env` copied into the test clone or the feature is shown to fail gracefully.

## 5. When verification fails: fix, then teach the skill

Loop, max 5 attempts per failure:
1. Read the actual error (`docker compose -p $P logs <service>`). Find the root cause, not the symptom.
2. Fix the repo files in the worktree. Re-run the full step 4 from a fresh clone.
3. Once green, decide whether the cause is **repo-specific** (only this codebase) or **generic** (would hit another repo of the same stack).
4. Generic cause: append an entry to `references/containers-traps.md` in the format shown there. If the fix contradicts an instruction in this file, correct that instruction instead of adding a trap, and note the change in the traps file.
5. Never record a trap that was not reproduced and then verified fixed. Never delete a trap without evidence it no longer applies.
6. Share it with the "Recording a lesson" section of build's SKILL.md (a PR to this plugin's source repo; never edit the installed copy).

After 5 failed attempts on one failure, stop, leave the worktree in place, and report the exact error and what was tried.

## 6. Report

- Verdict from step 1.
- Files written, worktree path, branch name.
- Verification output (the `ps -a` table, health response, second-start result, arm64 result).
- Traps added or skill lines changed during this run.
- What only the user can do: external keys, `docker login ghcr.io`, pushing the branch, opening the PR.
