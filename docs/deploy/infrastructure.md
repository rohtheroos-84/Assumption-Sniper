# Managed infrastructure for Assumption Sniper

## Recommended services

| Component | Dev (local) | Staging | Production |
|-----------|-------------|---------|------------|
| Postgres | `docker-compose` postgres:16 | Managed RDS / Cloud SQL / Neon | Managed HA Postgres |
| Redis | `docker-compose` redis:7 | Managed ElastiCache / Upstash | Managed Redis with TLS |
| API | Docker / uvicorn | Container service (2+ replicas) | Blue/green slots |
| Web | Docker / next dev | Container service (2+ replicas) | Blue/green slots |

## Connection strings

Copy `deploy/env/staging.env.example` or `deploy/env/production.env.example` and set:

- `DATABASE_URL` — use `postgresql+asyncpg://` for the async SQLAlchemy driver
- `REDIS_URL` — use `rediss://` (TLS) in staging/production

## Provisioning checklist

1. Create Postgres database and application user with least privilege (CRUD on app schema only).
2. Create Redis instance with password auth and TLS enabled.
3. Store `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, and `OPENROUTER_API_KEY` in your secrets manager.
4. Configure network security: API can reach Postgres/Redis; web reaches API only.
5. Enable automated backups (Postgres daily, 30-day retention per PRD).

## GitHub environments

Configure GitHub repository environments:

- **staging** — auto-deploy on merge to `main`
- **production** — requires manual approval; restricted to release managers

Required secrets per environment:

| Secret | Description |
|--------|-------------|
| `DATABASE_URL` | Managed Postgres connection string |
| `REDIS_URL` | Managed Redis connection string |
| `JWT_SECRET` | Signing key for access tokens |
| `OPENROUTER_API_KEY` | LLM provider key |
| `STAGING_API_URL` | Public staging API URL for smoke tests |
| `PRODUCTION_API_URL` | Public production API URL for smoke tests |

## Local docker stack

```bash
docker compose up --build
# API: http://localhost:8000
# Web: http://localhost:3000
```
