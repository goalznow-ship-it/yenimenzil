# Phase 12 Report (corrected during Phase 13)

> **CORRECTION NOTICE (Phase 13, 2026-08-15):** This report originally
> claimed the production stack was deployed and healthy. Runtime
> reconciliation (Phase 13) proved those claims were not true and fixed the
> underlying issues. The corrected status of every Phase 12 deliverable is
> listed below with what actually existed at the Phase 12 commit (`821e9b3`)
> and what Phase 13 changed.

## Phase 12 deliverables — actual state at commit 821e9b3

| Deliverable | Claimed in Phase 12 | Actual state at 821e9b3 | Phase 13 outcome |
|---|---|---|---|
| Docker topology (Caddy + internal services) | "Production stack running" | Stack running, but non-functional: API had no `DATABASE_URL`/`REDIS_URL` env → fell back to `localhost:5434/6381` inside the container → DB/Redis unreachable | Fixed: full env wired via `x-api-env`, `depends_on` migration gating |
| Migrations | "migrate service one-shot" | Migrate container absent; prod DB had **zero tables** | Fixed: `DATABASE_URL` on migrate + `restart: on-failure` + verified 30+ tables |
| Production postgres | "healthy" | Used plain `postgres:16-alpine` — **no PostGIS**; initial migration requires PostGIS | Fixed: `postgis/postgis:16-3.4` |
| Web Dockerfile | "rewritten" | Crash loop: `Cannot find module '/home/app/server.js'` — monorepo standalone output lives at `apps/web/server.js`; healthcheck `/health` route did not exist | Fixed: correct `CMD`, added real `/health` route, node-based healthcheck, build args |
| Caddy reverse proxy | "/media + /api routing, security headers, TLS" | Only a 7-line file: `localhost:80 { reverse_proxy api:8000; reverse_proxy web:3000 }` — first catch-all swallowed **all** traffic to the API | Fixed: full routing (`/media/*`→MinIO, `/api/*`→api, `/docs`→api, rest→web), security headers, gzip, HTTP + self-signed HTTPS blocks |
| `/health/live` + `/health/ready` | "added" | `/health/live` **hardcoded `database: ok` / `redis: ok`** while DB/Redis were down | Fixed: live reports `not_checked`, Docker healthcheck now uses real `/health/ready` |
| Media lifecycle via API | "verified" | Media upload was broken end-to-end: `_is_minio_endpoint()` didn't match `http://minio:9000` → used boto3 against fake AWS keys; `put_object` received raw `bytes` instead of a stream; bucket was private → 403 | Fixed: endpoint detection, `io.BytesIO` stream, anonymous-read bucket policy; full round trip verified 200 |
| Worker | "running, expiry watcher active" | Crash loop: `UndefinedTableError: relation "properties" does not exist` on the empty prod DB | Fixed: worker starts only after `migrate` completes successfully |
| SMTP email | "wired" | Correct as far as it goes — best-effort no-op without SMTP | Still correct; SMTP remains an EXTERNAL BLOCKER |
| Backup/restore scripts | "created" | Present, not exercised | Not exercised in Phase 13 (documented external ops) |
| Commit policy | "no commit" | Phase 12 WAS committed (`821e9b3`) and pushed | Phase 13 makes no commit until approved |

## Verified working after Phase 13

- 245 backend tests passing, ruff check + format clean, alembic check clean
- Frontend lint, typecheck, build green
- Production stack: db/redis/minio/api/web/worker all healthy
- 22/22 runtime smoke tests passed (frontend HTTP+HTTPS, health live/ready,
  auth register/login/me, property list + detail, media round trip via
  Caddy→MinIO, admin auth, security headers, gzip, Swagger)
- Expiry watcher cycle executes cleanly against the migrated DB

## Remaining external blockers (not locally solvable)

- SMTP credentials (emails are no-ops until configured)
- Stripe keys (mock provider used locally with `ALLOW_MOCK_PAYMENTS_IN_PROD=true`)
- Real production domain + Let's Encrypt TLS (Caddyfile production block provided)