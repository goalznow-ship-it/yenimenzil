# YeniMenzil.az — Roadmap

> This phase list is historical. Many backend and ecosystem items below are now
> implemented; use open issues and verified production checks for current
> prioritization instead of interpreting unchecked boxes as the live status.

## Phase 1 — Frontend foundation (current)

Frontend must look polished before any backend work.

- [x] Monorepo setup (pnpm + Turborepo)
- [x] Design system primitives
- [x] Global layout: Header (desktop/mobile), Footer, bottom mobile nav
- [x] Homepage: hero search (Al/Kirayə/Günlük), curated sections
- [x] PropertyCard
- [x] Realistic demo listings (Azerbaijani, AZN)
- [x] Search results page with URL-based filters + sticky map
- [x] Property detail page (gallery, contact card, price analysis)
- [x] Map UI foundation (MapLibre abstraction, demo markers)
- [x] Mobile responsiveness, skeletons, empty/error states
- [x] Lint / typecheck / build green

## Phase 2 — Backend foundation

- [ ] FastAPI app in `apps/api` (`/api/v1`)
- [ ] PostgreSQL + PostGIS via Docker Compose
- [ ] SQLAlchemy 2 models + Alembic migrations
- [ ] Redis (cache, counters, rate limiting)
- [ ] Property CRUD + validation (Pydantic v2)
- [ ] Location hierarchy data (city/district/settlement/metro)
- [ ] Authentication: email/password + phone OTP architecture, HTTP-only
      cookies, refresh tokens
- [ ] Favorites, saved searches
- [ ] Property creation flow (multi-step wizard)
- [ ] pytest suite (CRUD, permissions, API)

## Phase 3 — Ecosystem features

- [ ] Seller dashboard + analytics
- [ ] Admin/moderation panel with audit log
- [ ] Notifications (new matching, price drop, moderation)
- [ ] Internal messaging (property-linked, WebSocket later)
- [ ] Viewing appointments
- [ ] Price history + price intelligence
- [ ] Agencies, agents, new developments
- [ ] Property comparison (/compare, up to 4)
- [ ] Advanced maps: clustering, draw-polygon search, POIs
- [ ] SEO: JSON-LD, canonical URLs, sitemap, SEO slugs

## Phase 4 — Intelligence (only after core is stable)

- [ ] AI semantic search (natural-language → structured filters)
- [ ] AI property assistant (honest, clearly-labelled estimates)
- [ ] Price intelligence (median price/m² by district, comparisons)
- [ ] Recommendations
- [ ] Image intelligence (duplicate detection)
- [ ] Investment analytics (rental yield estimates)
- [ ] Trust scoring (explicitly derived from real signals only)

## Monetization (architecture-ready)

- [ ] Promotions: STANDARD / PREMIUM / VIP / TOP / URGENT — paid placement
      always clearly labelled ("Önə çıxarılıb" / "Reklam")
- [ ] Agency subscriptions (Basic / Professional / Business)
- [ ] Payments integration (gateway-agnostic)

## Demo infrastructure notes

- `docker-compose.yml` provides PostgreSQL (PostGIS), Redis, MinIO.
- `.env.example` documents every variable; real secrets never enter the repo.
