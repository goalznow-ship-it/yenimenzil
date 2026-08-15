# YeniMenzil.az Production Deployment Guide

## Overview

This document describes the production deployment of YeniMenzil.az, a marketplace backend application. The deployment uses Docker Compose with Caddy as a reverse proxy on ports 80/443.

---

## Architecture

### Production Topology

```
┌──────────────────────────────────────────────────────────────┐
│                    Public Internet (80/443)                   │
│  ┌─────────────────────┐  ┌──────────────────────────────┐ │
│  │                     Caddy                           │ │
│  │  - HTTPS (via Let's Encrypt or internal)              │ │
│  │  - /api/* → api:8000 (internal)                     │ │
│  │  - /media/* → minio:9000 (internal)                 │ │
│  │  - / → web:3000 (standalone Next.js)                │ │
│  └─────────────────────┘  └──────────────────────────────┘ │
│  └──────────────────────────────────────────────────────────────┘
│                        ↓                                       │
│                Internal Network (backend)                      │
│  ┌─────────────────────┐  ┌────────────────────────────────┐ │
│  │         db          │  │         redis          │ │
│  │  PostgreSQL 16      │  │  Redis 7 (in-memory)   │ │
│  │  - Volume: pg_data  │  │  - Volume: redis_data  │ │
│  └─────────────────────┘  └────────────────────────────────┘ │
│  └──────────────────────────────────────────────────────────────┘
│  ┌─────────────────────┐  ┌────────────────────────────────┐ │
│  │        minio         │  │         api          │ │
│  │  MinIO S3-compatible │  │  FastAPI + Alembic           │ │
│  │  - Volume: minio_data│  │  - Port: 8000 (internal)       │ │
│  │  - Console: 9001     │  │  - Health: /api/v1/health/live │ │
│  └─────────────────────┘  └────────────────────────────────┘ │
│  └──────────────────────────────────────────────────────────────┘
│  ┌─────────────────────┐  ┌────────────────────────────────┐ │
│  │        worker        │  │         web          │ │
│  │  Python worker      │  │  Next.js 16 (standalone)     │ │
│  │  - Expiry watcher   │  │  - Output: standalone          │ │
│  │  - CELERY_BROKER    │  │  - Port: 3000 (internal)     │ │
│  └─────────────────────┘  └────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Networks

- **frontend**: Caddy + web (api accessible via Caddy)
- **backend**: db + redis + minio + api + worker (all internal only)

### Services and Ports

| Service    | Ports    | Exposure  | Notes                        |
|------------|----------|-----------|------------------------------|
| caddy      | 80/443   | Public    | Reverse proxy, TLS termination|
| api        | 8000     | Internal  | FastAPI + SQLAlchemy + Alembic|
| web        | 3000     | Internal  | Next.js standalone render      |
| worker     | None     | Internal  | Celery background tasks       |
| minio      | 9000/9001| Internal  | S3-compatible storage          |
| db (postgres)| 5432   | Internal  | PostgreSQL with PostGIS        |
| redis      | 6379     | Internal  | Redis cache                    |

No services expose ports on the host except Caddy (80/443). All other services are internal-only.

---

## Prerequisites

### Hardware

- Minimum 2 CPU cores, 4GB RAM recommended
- Docker Engine 20.10+
- Docker Compose v2+

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
APP_ENV=production
DATABASE_URL=postgresql+asyncpg://user:pass@hostname:5432/dbname
REDIS_URL=redis://hostname:6379/0
SECRET_KEY=your-32-byte-secret-key-here

# Optional - with defaults
S3_ENDPOINT=http://minio:9000
S3_BUCKET=yenimenzil-media
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
# Media is served publicly through the Caddy reverse proxy, NOT directly
# from MinIO (MinIO has no host port in the production stack).
S3_PUBLIC_URL=https://yourdomain.com/media
S3_SECURE=false

SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-username
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
DEFAULT_FROM_EMAIL=no-reply@yourdomain.com

PAYMENT_PROVIDER=stripe
STRIPE_PUBLIC_KEY=your-public-key
STRIPE_SECRET_KEY=your-secret-key
STRIPE_WEBHOOK_SECRET=your-webhook-secret
ALLOW_MOCK_PAYMENTS_IN_PROD=false

NEXT_PUBLIC_API_URL=https://yourdomain.com/api/v1
NEXT_PUBLIC_APP_URL=https://yourdomain.com
NEXT_PUBLIC_USE_DEMO_DATA=false

CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### DNS

Configure DNS for your domain pointing to the server's public IP:
- `yourdomain.com` → A record → server IP
- `www.yourdomain.com` → A record → server IP

For local verification the stack serves plain HTTP on `localhost:80` and
HTTPS via Caddy's self-signed `tls internal` on `localhost:443` — no
`/etc/hosts` entry is required.

---

## Deployment

### 1. Clone the repository

```bash
git clone https://github.com/your-organization/yenimenzil.git
cd yenimenzil
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Build and start the stack

```bash
# Build all Docker images
docker compose -f docker-compose.prod.yml build

# Start the production stack
docker compose -f docker-compose.prod.yml up -d
```

### 3. Wait for services to become healthy

```bash
# Check status
docker compose -f docker-compose.prod.yml ps

# View logs for any issues
docker compose -f docker-compose.prod.yml logs -f
```

### 4. Run database migrations (auto-run on first start)

The `migrate` service runs `alembic upgrade head` on startup. If it doesn't run automatically:

```bash
docker compose -f docker-compose.prod.yml up -d migrate
```

### 5. Verify the deployment

```bash
# Health checks
curl -fsS https://yourdomain.com/api/v1/health/live
curl -fsS https://yourdomain.com/api/v1/health/ready

# API docs (Swagger UI, routed through Caddy)
curl -fsS https://yourdomain.com/docs
```

---

## Production Checklist

### Before Going Live

- [ ] Set `APP_ENV=production` in `.env`
- [ ] Change `SECRET_KEY` to a strong 32-byte random value
- [ ] Configure `DATABASE_URL` to point to production PostgreSQL
- [ ] Configure `REDIS_URL` to point to production Redis
- [ ] Set `ALLOW_MOCK_PAYMENTS_IN_PROD=false` (or configure real payment provider)
- [ ] Configure SMTP credentials for transactional emails
- [ ] Set `S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` for media storage
- [ ] Configure `CORS_ORIGINS` with production domains
- [ ] Set `NEXT_PUBLIC_USE_DEMO_DATA=false`
- [ ] Configure domain DNS to point to server IP
- [ ] Obtain SSL certificate (Caddy will auto-obtain via Let's Encrypt if DNS is configured)
- [ ] Test payment provider (mock only allowed in staging with `ALLOW_MOCK_PAYMENTS_IN_PROD=true`)
- [ ] Run full backup
- [ ] Verify all health endpoints return 200

### After Going Live

- [ ] Monitor Caddy logs for HTTPS certificate renewal
- [ ] Monitor database performance and connection pool
- [ ] Monitor Redis memory and hit rate
- [ ] Monitor MinIO storage usage
- [ ] Check worker task processing logs
- [ ] Verify email delivery (password resets, verification)
- [ ] Run periodic backup (daily/weekly)

---

## Backup & Restore

### Backup

```bash
# Run the backup script
./scripts/backup.sh
```

Backups are stored in `/tmp/`:
- `pg_backup_YYYYMMDD_HHMMSS.sql` - PostgreSQL database dump
- `minio_backup_YYYYMMDD_HHMMSS.tar` - MinIO media data archive

### Restore

```bash
# Run the restore script
./scripts/restore.sh
```

Follow the prompts to select which backups to restore.

### Manual Backup/Restore

```bash
# Database backup
docker compose -f docker-compose.prod.yml exec db pg_dump -U yenimenzil -d yenimenzil > backup.sql

# Database restore
cat backup.sql | docker compose -f docker-compose.prod.yml exec db psql -U yenimenzil -d yenimenzil

# MinIO backup
docker compose -f docker-compose.prod.yml exec minio tar czf - /data > minio_backup.tar

# MinIO restore
cat minio_backup.tar | docker compose -f docker-compose.prod.yml exec minio tar xzf - -C /data
```

---

## Development vs Production

### Development (docker-compose.yml)

- Uses the original `docker-compose.yml` from the repo
- Ports mapped to host: postgres 5432, redis 6379, minio 9000/9001
- MinIO healthcheck fixed to port 9000 (was 9002)
- Web depends on api without `service_healthy` condition
- Intended for local development only

### Production (docker-compose.prod.yml)

- Separate compose project `yenimenzil-prod`
- No host port exposures except Caddy (80/443)
- Separate networks to avoid conflicts with existing containers
- Volume namespaced with project name
- Migration service runs one-shot `alembic upgrade head`
- Caddy reverse proxy with internal only services

### Key Differences

| Aspect              | Development          | Production          |
|---------------------|---------------------|---------------------|
| Project name        | implicit "yenimenzil" | "yenimenzil-prod"   |
| Host port exposures | postgres:5432, redis:6379, minio:9000-9001 | None (Caddy only: 80/443) |
| Networks            | shared "yenimenzil-net" | frontend + backend  |
| Restart policies    | unless-stopped      | unless-stopped      |
| Migration strategy  | manual or auto      | one-shot service    |
| Caddy config        | simple or none      | full with security headers |

---

## API Endpoints

### Health

```
GET /api/v1/health/live  - Liveness check (process up, no deps)
GET /api/v1/health/ready - Readiness check (DB + Redis reachable)
GET /api/v1/health       - Combined health check (503 on failure)
```

### Authentication

```
POST /api/v1/auth/register     - Register new user
POST /api/v1/auth/login        - Login
POST /api/v1/auth/verify-email - Email verification
POST /api/v1/auth/password-reset - Password reset
```

### Listings

```
GET  /api/v1/listings          - List listings (with pagination/filter)
GET  /api/v1/listings/{id}     - Get listing by ID
POST /api/v1/listings          - Create new listing
PUT  /api/v1/listings/{id}     - Update listing
DELETE /api/v1/listings/{id} - Delete listing
```

### Media

```
GET /media/{bucket}/{object}   - Serve media via Caddy proxy
POST /api/v1/upload            - Upload file (S3/MinIO)
```

### Payments

```
POST /api/v1/payments/top-up   - Create payment intent
POST /api/v1/payments/webhook  - Payment webhook receiver
```

---

## Deployment Troubleshooting

### Common Issues

1. **Caddy won't start** — Check Caddyfile syntax and TLS configuration
2. **API returns 503** — Check that DB and Redis are healthy (`/health/live` should return 200)
3. **Web can't connect to API** — Verify Caddy is running and config forwards /api/* to api:8000
4. **MinIO healthcheck fails** — Ensure minio healthcheck path `/minio/health/live` is correct
5. **Migrations failed** — Check migrate service logs: `docker compose logs migrate`
6. **Email not sending** — Verify SMTP credentials and that `SMTP_HOST` is set in `.env`
7. **Playwright E2E fails** — Chromium is available at `/usr/bin/chromium`; playwright not installed

### Logs

```bash
# View all service logs
docker compose -f docker-compose.prod.yml logs

# View specific service logs
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f caddy
docker compose -f docker-compose.prod.yml logs -f worker
```

### Debug Shell

```bash
# Exec into a running service
docker compose -f docker-compose.prod.yml exec db psql -U yenimenzil -d yenimenzil
docker compose -f docker-compose.prod.yml exec api python -c "from app.core.config import get_settings; print(get_settings().APP_ENV)"
docker compose -f docker-compose.prod.yml exec worker python -c "
import asyncio
from app.services.expiry_watcher import _check_expiring_properties, _check_expiring_promotions
asyncio.run(_check_expiring_properties()); asyncio.run(_check_expiring_promotions())
"
```

---

## Migration Notes

### From Development to Production

1. Set `APP_ENV=production` in `.env`
2. Change `SECRET_KEY` (must not be the default)
3. Configure `DATABASE_URL` for production PostgreSQL (not localhost:5432)
4. Set `ALLOW_MOCK_PAYMENTS_IN_PROD=false` unless staging
5. Configure SMTP for transactional emails
6. Configure S3/MinIO credentials
7. Set `CORS_ORIGINS` to production domains only
8. Set `NEXT_PUBLIC_USE_DEMO_DATA=false`
9. Run `docker compose -f docker-compose.prod.yml up -d` for first deployment
10. Verify all health endpoints

### Rollback

1. `docker compose -f docker-compose.prod.yml down`
2. Restore from backup: `./scripts/restore.sh`
3. Re-deploy previous image versions if needed
4. Verify data integrity

---

## Security Considerations

### Hardened Settings

- `SECRET_KEY` must be a strong random value (not `change-me-in-production`)
- `DATABASE_URL` must not use `localhost` in production
- `CORS_ORIGINS` must not contain `localhost` in production
- `PAYMENT_PROVIDER=mock` forbidden in production without `ALLOW_MOCK_PAYMENTS_IN_PROD=true`
- SMTP credentials should be external secrets, not in `.env` if possible
- All internal services have no host port exposures
- Caddy security headers enabled (X-Content-Type-Options, X-Frame-Options, etc.)
- Request body size limited to 20MB

### Data Protection

- Regular backups of PostgreSQL and MinIO
- Backup retention policy (recommended: 30 days)
- Encrypt backup files at rest
- Database connections use SSL/TLS in production
- No secrets stored in Docker images (read from environment at runtime)

---

## One-Command Operations

### Start Stack

```bash
docker compose -f docker-compose.prod.yml up -d
```

### Stop Stack

```bash
docker compose -f docker-compose.prod.yml down
```

### Restart Services

```bash
docker compose -f docker-compose.prod.yml restart
```

### Rebuild Images

```bash
docker compose -f docker-compose.prod.yml build
```

### View Logs

```bash
docker compose -f docker-compose.prod.yml logs -f
```

### Run Migrations

```bash
docker compose -f docker-compose.prod.yml up -d migrate
```

### Create Backup

```bash
./scripts/backup.sh
```

### Create Restore

```bash
./scripts/restore.sh
```

---

## Version History

### Phase 12 - Initial Release

- Production Docker topology with Caddy reverse proxy
- Production Dockerfiles (api, worker, web)
- Config fail-fast validation
- Health endpoints (/live, /ready)
- Email service (smtplib-based)
- Request correlation ID middleware
- Structured logging (python-json-logger)
- boto3 added to production dependencies
- Payment mock guard (ALLOW_MOCK_PAYMENTS_IN_PROD)
- Dev compose.yml healthcheck fixes
- Caddyfile production config
- Backup/restore scripts
- Full DEPLOYMENT.md documentation