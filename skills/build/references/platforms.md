# Platform gotchas: Cloudflare Workers, trigger.dev, Supabase and Postgres

Each line was hit on a real project (2026-05 to 2026-10) and its fix verified.
Read the section for the platform you are touching before writing or
deploying. Deploys, secret changes and schedule changes need the user's go-ahead
every time; an approval does not carry over to the next action.

## Cloudflare Workers (wrangler)

Deploy and recover:
- Check the target before deploying: `npx wrangler whoami`. A `wrangler.jsonc`
  without `account_id` deploys to whatever account the login or
  `CLOUDFLARE_API_TOKEN` resolves to.
- `npx wrangler deployments status` shows which version is serving.
  `npx wrangler deployments list`, then `npx wrangler rollback -y -m "<reason>"`.
  `npx wrangler tail --format json` streams live requests.
- After a rollback the latest uploaded version is not the deployed one, and
  `wrangler secret put` refuses until something is deployed.
  `wrangler versions secret put <NAME>` works either way.
- A smoke check alone passed a broken deploy. Run a real regression against the
  live URL after deploying and roll back on failure. Re-run once after ~30 s
  before rolling back: a Durable Object reset during switchover failed good
  deploys.
- A brand-new `workers.dev` hostname can return 404 or error 1042 right after the
  first deploy. Retry the smoke check a few times, 15 s apart.
- `workers.dev` can serve the previous build for a minute or two, and the first
  upstream call can return 520. Wait and retest before chasing a bug.
- Deploying over the REST API without wrangler: the `workers.dev` subdomain must
  be enabled explicitly (`POST .../subdomain`) or the Worker returns 1042, and
  FormData Blob parts need filenames or the API returns 10021.
- Gitignore `.wrangler/`. A `git add -A` after a deploy once swept its cache into
  main. Stage files by name.

Secrets:
- Secrets go in `wrangler secret put`, never `[vars]`: vars are plain text in
  the config and the dashboard.
- Feed values on stdin from a file (`npx wrangler secret put NAME < "$f"`), never
  as an argument. Stage them in a `mktemp -d` created under `umask 077`.
- Secrets are per Worker. A new value reaches a Worker only on its next deploy
  or a `secret put` on that Worker. Several Workers built from one codebase each
  need their own deploy; deploying one does not update the others.
- `secret put` only adds or updates. Secrets that are bound but no longer used
  stay until you `wrangler secret delete` them.
- Fail closed: a Worker whose auth secret is missing should return 503 to
  everyone, not serve ungated.

Runtime:
- An uncaught throw returns Cloudflare's 1101 HTML error page instead of your
  JSON. Wrap every route handler.
- Some bindings (the `worker_loaders` sandbox, for one) need Workers Paid; on the
  free plan the deploy fails with error 10195.
- Never exercise an OAuth upstream with rotating refresh tokens from
  `wrangler dev`. A local refresh consumes the token the deployed Worker holds.
- A bare curl to a streamable-HTTP MCP endpoint gets
  `400 Mcp-Session-Id header is required`. That is the protocol, not an outage:
  send `initialize` first.

## trigger.dev (v4)

Writing tasks:
- `maxDuration` counts compute time only, so a hung `await` can leave a run
  EXECUTING for nearly an hour. Loops that call external services need their
  own wall-clock deadline (`Date.now()` checks).
- Fail loudly. A scrape that returns 0 results must throw. A report job whose
  send failed kept showing "completed" for weeks until the failed send was made
  to throw.
- Make reruns safe in the data: skip rows already marked done, write with
  `upsert(..., { onConflict })`. Retries and manual replays then cost nothing.
- Chain stages in code (the scraper calls `next.trigger(...)` after a successful
  run) rather than with separate crons that assume timing.
- Write crons in UTC with the local time in a comment:
  `cron: "0 11 * * *", // 6am ET`.
- Import the bare `@trigger.dev/sdk`; `@trigger.dev/sdk/v3` is the old path.
- Tasks read runtime keys from `process.env`. List the required ones in the file
  header. Env vars are set on the project, not passed at deploy, and new runs
  pick up a changed value without a redeploy.

Deploying:
- Schedules declared in code are registered and removed by each deploy. Count
  schedules and list tasks before and after; a task that disappeared means the
  wrong checkout was deployed.
- A deploy ships the whole checkout. A deploy from one feature branch reverted
  another branch's live change for two hours. Make sure HEAD contains what is
  live first: `git merge-base --is-ancestor <live sha> HEAD`.
- Commit before deploying; the deployment record shows `git.dirty`.
- Two files with the same name anywhere in one project's task directories break
  the build with "Two output files share the same path" (`*.test.ts` excluded).
- The CLI needs a lockfile ("No lockfile found"). Pin the SDK and the CLI to the
  same exact version; an `npx trigger.dev@latest` script silently drifts.
- A secret key belongs to one project. "Invalid project ref for this API key"
  means the key is from another project. Unset stray `TRIGGER_SECRET_KEY` and
  `TRIGGER_PROJECT_ID` in the deploy shell so the config file picks the project.
- Roll back by redeploying the last good sha. In-flight runs keep the version
  they started on.
- A wrapper that injects secrets into a command can also inject a stale
  `GITHUB_TOKEN`/`GH_TOKEN`, which git and gh prefer. Run `git fetch` and
  `git push` outside it.

## Supabase and Postgres

Migrations:
- Merging to main applies nothing unless CI does it. Read the workflow before
  assuming a migration is live, and check the live schema after.
- Write migrations idempotent (`IF NOT EXISTS`). Wrap changes to tables that
  exist only in production in `DO $$ BEGIN IF EXISTS (SELECT 1 FROM
  information_schema.tables ...) THEN ... END IF; END $$`, so they also run on a
  fresh local stack.
- A new schema needs `GRANT USAGE ON SCHEMA s TO service_role` and
  `GRANT ALL ON ALL TABLES IN SCHEMA s TO service_role`, and it must be in the
  API's exposed schemas (`PGRST_DB_SCHEMAS` when self-hosted) to be reachable over
  `/rest/v1`. Local and production lists often differ, so a route can 404 locally.
- On a big table never `ADD CONSTRAINT ... UNIQUE` directly. Run
  `CREATE UNIQUE INDEX CONCURRENTLY`, then `ADD CONSTRAINT ... USING INDEX`.
  Before adding it, find every write path without `ON CONFLICT`; each will start
  throwing.
- Before adding a new status value, read the column's CHECK constraint. A new
  value outside it broke every write to a shared table.
- Functions owned by `supabase_admin` (and all of `auth.*` and `storage.*`)
  cannot be replaced from a normal login. Use the dashboard SQL editor, then
  confirm with a read-only check of the function body.

Timeouts and load:
- The API roles have short statement timeouts (8 s on the instance this was hit
  on), which surface as HTTP 500 with code `57014`. A trigger on every update
  (a search-vector refresh, say) makes bulk upserts hit it: skip no-op updates
  and send small chunks. 500-row chunks to 50 took one update from 12 s to 0.28 s.
- A TCP proxy in front of the database can kill queries after a few minutes,
  whatever the client. Run bulk DML in the SQL editor or as a server-side
  function.
- Never hammer the dashboard's query endpoint (pg-meta `/pg/query`) with batch
  scripts. That took down the dashboard and every app on the instance.
- Planner statistics go stale (`n_live_tup = 0` on a full table). Run `ANALYZE`
  or a real `count(*)` before calling a table empty.

Schema drift:
- Check the live table, not the repo's DDL. Drift goes both ways, and a column
  that exists only in the repo fails with `42703`.
- Connections without a `search_path` need schema-qualified names (`app.users`).

RLS:
- Policy helpers: `security definer`, `set search_path = public`, `revoke all ...
  from public`, `grant execute ... to authenticated`. Policies say
  `to authenticated` and call `(select auth.uid())`, which is evaluated once per
  statement instead of once per row.
- RLS only guards traffic that goes through the API as a user. A server holding a
  direct `pg` connection or the service-role key bypasses it, so that server must
  do its own authorization.

Edge functions (self-hosted):
- A global `VERIFY_JWT: false` makes a per-function `verify_jwt = true` in
  `config.toml` do nothing. Each function must check its own bearer secret.
- The runtime kills a worker at its wall-clock limit (60 s on the stack this was
  hit on). Long jobs become a queue that `pg_cron` ticks, with `pg_net` calling the
  function using a bearer it reads from `supabase_vault`.
- A new env var must be added to the functions service in the compose file AND
  on the host platform, or it is empty in one of them.

Connections:
- If connections are refused after an infra change, suspect a stale host or port
  in the stored connection string before suspecting the database.
