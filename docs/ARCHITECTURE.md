# YeniMenzil.az — Architecture

## 1. Overview

YeniMenzil.az is a production-grade Azerbaijani real-estate marketplace. It is a
pnpm + Turborepo monorepo with a Next.js web application and a Python/FastAPI
backend, sharing typed contracts and a design system.

Brand positioning: **"YeniMenzil.az — Yeni məkanını burada tap."**

The platform covers apartments, new and old buildings, houses, villas, land,
offices, commercial properties, garages and new developments, with three deal
types: sale, long-term rent and daily rent.

## 2. Repository layout

```
yenimenzil/
├── apps/
│   ├── web/          # Next.js 16 (App Router) — frontend
│   └── api/          # FastAPI — backend (Phase 2)
├── packages/
│   ├── ui/           # Design system components
│   ├── types/        # Shared TypeScript types (mirror of backend schemas)
│   ├── config/       # Shared app/tailwind configuration
│   ├── eslint-config/# Shared ESLint configuration
│   └── typescript-config/ # Shared tsconfig presets
├── infra/
│   ├── docker/       # Container definitions
│   └── caddy/        # Reverse proxy configuration (production, see deploy/Caddyfile)
├── docs/             # Architecture, database, API, design system, roadmap
├── docker-compose.yml
├── pnpm-workspace.yaml
└── turbo.json
```

## 3. Technology stack

### Frontend (apps/web)

- Next.js 16 (App Router, Server Components, SSR)
- React 19, TypeScript (strict)
- Tailwind CSS 4
- shadcn/ui style primitives built on Radix UI
- Lucide icons
- TanStack Query (client data fetching where needed)
- React Hook Form + Zod (forms)
- Framer Motion (subtle motion only)
- Zustand only where genuine cross-page state is required (e.g. favorites)
- MapLibre GL (map rendering, behind an abstraction layer)

### Backend (apps/api — Phase 2)

- Python 3.12+, FastAPI, async
- SQLAlchemy 2 + Alembic
- PostgreSQL + PostGIS
- Redis (cache, counters, rate limiting)
- Pydantic v2
- API versioned under `/api/v1`

### Infrastructure

- Dev: Docker Compose — PostgreSQL (PostGIS), Redis, MinIO
- Prod (later): Nginx, Cloudflare, S3/R2, managed PostgreSQL/Redis

Business logic must never be coupled to infrastructure vendors.

## 4. Frontend architecture

Feature-oriented structure:

```
apps/web/
├── app/                  # Routes (App Router)
├── components/
│   ├── ui/               # Primitives (Button, Input, Select, …)
│   ├── layout/           # Header, Footer, mobile nav
│   └── common/           # Shared composite components
├── features/             # Feature modules
│   ├── properties/       # PropertyCard, detail, gallery
│   ├── search/           # Filters, results
│   ├── map/              # MapLibre abstraction
│   ├── favorites/        # Favorites store
│   └── …
├── lib/                  # Utilities, formatting, seo
├── hooks/
├── services/             # API clients
├── types/
└── styles/
```

Rules:

- Prefer Server Components; client components only where interactivity is
  needed.
- Search/filter state lives in the URL (sharing, SEO, history, saved searches).
- No unnecessary global state.
- Property media dominates the visual experience.

## 5. Map architecture

MapLibre GL behind an abstraction (`lib/map` / `features/map`) so the provider
can be swapped without touching business code. Phase 1 uses demo tiles with
local markers; later phases add clustering, draw-search (polygon), radius
search and POI layers. The map must never block first render (lazy loading).

## 6. Data flow (Phase 1)

Phase 1 has no backend. All listing data lives in `apps/web/src/data/` (typed
demo seed). The `services/` layer defines the future API contract so the swap
to the real backend is mechanical. `packages/types` holds the shared property
model used by both frontend and (later) the API.

## 7. Security principles

- OWASP best practices; no secrets in the repo (see `.env.example`).
- Backend is the source of truth for authorization (RBAC) — never trust the
  frontend.
- HTTP-only cookies + refresh tokens, rate limiting, hashed passwords.
- File uploads validated (MIME, dimensions, metadata stripping), signed
  object-storage uploads.

## 8. Localization

`az` is the default and primary language; `en` and `ru` are first-class from
day one. All user-facing copy is centralised for translation.
