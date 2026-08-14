# YeniMenzil.az

Azərbaycan üzrə daşınmaz əmlak elanları üçün full-stack marketplace. Layihə
Next.js frontend, FastAPI backend, PostgreSQL/PostGIS, Redis və S3-uyğun media
saxlama qatından ibarətdir.

## Texnologiyalar

- Next.js 16, React 19, TypeScript və Tailwind CSS
- FastAPI, SQLAlchemy 2 və Alembic
- PostgreSQL 16 + PostGIS
- Redis
- MinIO/S3
- pnpm workspace və Turborepo

## Lokal quraşdırma

Tələblər: Node.js 20.9+, pnpm 10.12.1, Python 3.12+ və Docker.

```bash
cp .env.example .env
corepack pnpm install --frozen-lockfile
docker compose up -d postgres redis minio
```

Backend:

```bash
cd apps/api
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"
.venv/Scripts/alembic upgrade head
.venv/Scripts/uvicorn app.main:app --reload
```

Frontend başqa terminalda:

```bash
corepack pnpm --filter @yenimenzil/web dev
```

- Sayt: `http://localhost:3000`
- API sənədləri: `http://localhost:8000/docs`
- Web healthcheck: `http://localhost:3000/health`
- API readiness: `http://localhost:8000/api/v1/health/ready`

Demo məlumatlarından istifadə etmək üçün `NEXT_PUBLIC_USE_DEMO_DATA=true`, real
API üçün isə `false` təyin edin.

## Keyfiyyət yoxlamaları

```bash
corepack pnpm lint
corepack pnpm typecheck
corepack pnpm build
cd apps/api && .venv/Scripts/pytest app/tests -q
docker compose config --quiet
```

## Production deploy

`docker-compose.prod.yml` Caddy, web, API, worker, migration, PostGIS, Redis və
MinIO servislərini başladır. Deploy-dan əvvəl ən azı aşağıdakı dəyişənlər real
və güclü dəyərlərlə verilməlidir:

- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `SITE_ADDRESS`
- `CORS_ORIGINS`
- `NEXT_PUBLIC_API_URL`
- SMTP dəyişənləri (hesab təsdiqi və şifrə bərpası üçün)

```bash
docker compose -f docker-compose.prod.yml config
docker compose -f docker-compose.prod.yml up -d --build
```

Ətraflı məlumat üçün [DEPLOYMENT.md](DEPLOYMENT.md) və
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) sənədlərinə baxın. Real sirlər
repository-yə commit edilməməlidir.
