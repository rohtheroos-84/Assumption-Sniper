# local setup

## prerequisites
- node 20 (see .nvmrc)
- pnpm 9
- python 3.11 (see .python-version)
- postgres 14+
- redis 7+

## frontend (apps/web)
1. pnpm install
2. pnpm -C apps/web dev

## backend (apps/api)
1. python -m venv .venv
2. .venv\\Scripts\\activate (windows) or source .venv/bin/activate (mac/linux)
3. pip install -r apps/api/requirements.txt -r apps/api/requirements-dev.txt
4. python -m uvicorn app.main:app --reload --app-dir apps/api

## initialize database

run the baseline schema creation script once after postgres is running:

```
python -m apps.api.scripts.init_db
```

## common scripts
- lint web: pnpm -C apps/web lint
- typecheck web: pnpm -C apps/web typecheck
- test web: pnpm -C apps/web test
- lint api: ruff check apps/api
- format api: ruff format apps/api
- test api: pytest -q apps/api

## environment
copy `.env.example` to `.env` and fill values for local development.

## docker (full stack)

```bash
docker compose up --build
```

- API: http://localhost:8000
- Web: http://localhost:3000
- Postgres and Redis start automatically

See `docs/deploy/infrastructure.md` for staging/production managed services.

## deployment

- Staging: merges to `main` trigger CD workflow (`.github/workflows/cd.yml`)
- Production: manual `workflow_dispatch` with environment approval
- Scripts: `deploy/deploy.sh`, `deploy/rollback.sh`
- Smoke tests: `python apps/api/scripts/smoke_test.py --url http://localhost:8000`
