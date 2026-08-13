# YeniMenzil.az Production Deployment Documentation

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Environment Configuration](#environment-configuration)
4. [Docker Stack Deployment](#docker-stack-deployment)
5. [Production Checklist](#production-checklist)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Rollback Procedure](#rollback-procedure)
8. [Monitoring and Observability](#monitoring-and-observability)

---

## Prerequisites

Before deploying to production, ensure you have:

- [ ] AWS/GCP/Azure account or self-hosted infrastructure
- [ ] Domain name: `api.yenimenzil.az` and `yenimenzil.az`
- [ ] SSL/TLS certificates (Let's Encrypt or purchased)
- [ ] PostgreSQL 16+ with PostGIS extension (managed or self-hosted)
- [ ] Redis 7+ (managed or self-hosted)
- [ ] Object storage: MinIO, AWS S3, or Cloudflare R2
- [ ] SMTP service for transactional emails
- [ ] Certificate authority access for Nginx proxy

---

## Infrastructure Setup

### Option A: Full Docker Compose (Recommended for VPS)

1. Clone the repository to your production server
2. Copy `.env.example` to `.env` and fill in all production values
3. Place SSL certificates at `./nginx/certs/api.yenimenzil.az.crt` and `.key`
4. Run the full stack:

```bash
docker compose -f docker-compose.yml up -d
```

### Option B: Kubernetes

The application is Kubernetes-ready with the following Deployment manifests:

- `api-deployment.yaml` - FastAPI application
- `web-deployment.yaml` - Next.js application
- `postgres-statefulset.yaml` - PostgreSQL with PostGIS
- `redis-statefulset.yaml` - Redis
- `minio-deployment.yaml` - Object storage

---

## Environment Configuration

Copy `.env.example` to `.env` and configure all variables:

### Critical Production Settings

| Variable | Required | Description |
|----------|----------|-------------|
| `APP_ENV` | Yes | Must be `"production"` |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `SECRET_KEY` | Yes | 32+ random bytes, never reuse |
| `CORS_ORIGINS` | Yes | Production frontend domain(s) |
| `NEXT_PUBLIC_API_URL` | Yes | `https://api.yenimenzil.az/api/v1` |
| `NEXT_PUBLIC_APP_URL` | Yes | `https://yenimenzil.az` |
| `SMTP_HOST` | Yes | SMTP server hostname |
| `SMTP_USERNAME` | Yes | SMTP authentication username |
| `SMTP_PASSWORD` | Yes | SMTP authentication password |
| `PAYMENT_PROVIDER` | Yes | `stripe` or `payme` |
| `STRIPE_PUBLIC_KEY`/`STRIPE_SECRET_KEY` | If Stripe | Payment provider keys |
| `STRIPE_WEBHOOK_SECRET` | If Stripe | Webhook verification secret |

### MinIO/S3 Settings

| Variable | Development | Production |
|----------|-------------|------------|
| `S3_ENDPOINT` | `localhost:9002` | Your S3 endpoint (e.g., `s3.amazonaws.com`) |
| `S3_SECURE` | `false` | `true` for production |
| `S3_BUCKET` | `yenimenzil-media` | Your bucket name |

---

## Docker Stack Deployment

### Start the full production stack

```bash
docker compose -f docker-compose.yml up -d
```

### Service Order

1. **postgres** - Starts first (required by all other services)
2. **redis** - Starts next (required by API, worker)
3. **minio** - Starts after Redis (required by API for media)
4. **api** - Starts after PostgreSQL, Redis, and MinIO are healthy
5. **web** - Starts after API is healthy
6. **worker** - Starts after all infrastructure is healthy
7. **adminer** - Optional, for database administration
8. **redis-exporter** - Optional, for metrics

### Verify Services are Healthy

```bash
# Check all service statuses
docker compose ps

# Check health status specifically
docker compose ps --format "table {{.Name}}\t{{.State}}\t{{.HealthStatus}}"

# View logs for any problematic service
docker compose logs -f api
```

### Stop the Stack

```bash
docker compose down
# Or stop without removing volumes
docker compose stop
```

---

## Production Checklist

### Before First Deployment

- [ ] Set `APP_ENV=production` in `.env`
- [ ] Generate a new `SECRET_KEY` with `openssl rand -base64 32`
- [ ] Configure `DATABASE_URL` to point to production PostgreSQL
- [ ] Configure `REDIS_URL` to point to production Redis
- [ ] Set `CORS_ORIGINS` to your production frontend domain
- [ ] Configure SMTP credentials for email delivery
- [ ] Set up payment provider keys (Stripe/Payme)
- [ ] Create the S3/MinIO bucket before first run
- [ ] Obtain and place SSL certificates for Nginx
- [ ] Set `ALLOWED_HOSTS` in the API configuration if needed
- [ ] Verify database migrations run successfully: `alembic upgrade head`

### After First Deployment

- [ ] Test health endpoint: `GET /api/v1/health`
- [ ] Test authentication flow (register + login)
- [ ] Test image upload to MinIO/S3
- [ ] Verify Redis rate limiting works
- [ ] Confirm email delivery (send test email)
- [ ] Check Nginx reverse proxy is routing correctly
- [ ] Verify HTTPS is working end-to-end
- [ ] Monitor logs for errors during first hour
- [ ] Test backup creation: `python -m app.core.backup`

### Ongoing Operations

- [ ] Monitor backup health daily
- [ ] Rotate backups per retention policy (30 days default)
- [ ] Renew SSL certificates before expiration
- [ ] Monitor Redis memory and rate limiter performance
- [ ] Review application logs for anomalies
- [ ] Update dependencies regularly (security patches)
- [ ] Review payment provider dashboard for failures

---

## Rollback Procedure

### Rollback to Previous Version

1. Stop the current services:
   ```bash
   docker compose down
   ```

2. Pull the previous Docker image tag:
   ```bash
   docker pull yenimenzil/api:previous-tag
   ```

3. Restart with the previous version:
   ```bash
   docker compose up -d
   ```

4. If database rollback is needed:
   ```bash
   # Downgrade alembic migration
   docker compose exec api alembic downgrade <previous_revision>
   ```

5. Verify the system is functional:
   ```bash
   docker compose exec api python -c "from app.main import app; print('App OK')"
   ```

### Emergency Rollback (Database Preservation)

If you need to preserve data while rolling back the code:

```bash
# 1. Create a backup first
docker compose exec postgres pg_dump -U yenimenzil yenimenzil > backup_$(date +%Y%m%d).sql

# 2. Downgrade the database
docker compose exec api alembic downgrade <previous_revision>

# 3. Restart services
docker compose up -d
```

---

## Monitoring and Observability

### Logs

All services output structured JSON logs when `APP_ENV=production`. To view:

```bash
# API logs
docker compose logs -f api

# Worker logs
docker compose logs -f worker

# MinIO logs
docker compose logs -f minio
```

### Metrics

- **Redis Exporter**: Available at `http://localhost:9121/metrics`
- **PostgreSQL**: Monitor via `pg_stat_activity`
- **Application Health**: `GET /api/v1/health`

### Health Checks

The API service exposes a health endpoint:

```
GET /api/v1/health
```

Returns:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "minio": "connected"
}
```

### Alerting Recommendations

- **Disk usage** > 80% on any service volume
- **Memory usage** > 90% on worker container
- **Rate limiter** triggers (investigate potential abuse)
- **Email send failures** (notify admin)
- **Payment provider** webhook failures
- **Backup failures** (critical - alert immediately)

---

## Development to Production Workflow

1. **Feature branch** → push to GitHub
2. **CI pipeline** runs: lint → typecheck → test → build → docker validate
3. **Merge to `main`** triggers production deployment
4. **Deploy** via `docker compose up -d` on production server
5. **Smoke test** health endpoint and critical flows
6. **Monitor** for 30 minutes, then mark as successful deployment