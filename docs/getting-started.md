# Getting started

## Prerequisites

- Node 20 (see `.nvmrc`)
- pnpm 9
- Python 3.11 (see `.python-version`)
- PostgreSQL 14+
- Redis 7+

## Frontend (`apps/web`)

```bash
pnpm install
pnpm -C apps/web dev
```

Web app: http://localhost:3000

## Backend (`apps/api`)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r apps/api/requirements.txt -r apps/api/requirements-dev.txt
python -m uvicorn app.main:app --reload --app-dir apps/api
```

API: http://localhost:8000

## Initialize database

Run once after PostgreSQL is available:

```bash
python -m apps.api.scripts.init_db
```

## Environment

Copy `.env.example` to `.env` and fill values for local development.

Key variables: `DATABASE_URL`, `REDIS_URL`, `OPENROUTER_API_KEY`, `JWT_SECRET`.

## Docker (full stack)

```bash
docker compose up --build
```

- API: http://localhost:8000
- Web: http://localhost:3000
- Postgres and Redis start automatically

## Common commands

| Task | Command |
|------|---------|
| Lint web | `pnpm -C apps/web lint` |
| Typecheck web | `pnpm -C apps/web typecheck` |
| Test web | `pnpm -C apps/web test` |
| Lint API | `ruff check apps/api` |
| Format API | `ruff format apps/api` |
| Test API | `pytest -q apps/api` |
| Smoke test | `python apps/api/scripts/smoke_test.py --url http://localhost:8000` |
| Exit criteria | `python apps/api/scripts/verify_exit_criteria.py` |

## Deployment

- Staging: merges to `main` trigger CD (`.github/workflows/cd.yml`)
- Production: manual `workflow_dispatch` with environment approval
- Scripts: `deploy/deploy.sh`, `deploy/rollback.sh`
- Infrastructure: `docs/deploy/infrastructure.md`
- Launch checklist: `docs/deploy/launch-checklist.md`

## Next steps

- Architecture: `docs/architecture.md`
- Full doc index: `docs/README.md`
- Product requirements: `PRD.md`
