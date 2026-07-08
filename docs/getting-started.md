# Setup guide

Complete instructions for running Assumption Sniper locally and preparing for deployment.

**Doc index:** [index.md](index.md) | **Project summary:** [project-complete.md](project-complete.md)

---

## Prerequisites

| Tool | Version | Reference |
|------|---------|-----------|
| Node.js | 20 | `.nvmrc` |
| pnpm | 9 | `package.json` |
| Python | 3.11 | `.python-version` |
| PostgreSQL | 14+ | Required for API |
| Redis | 7+ | Required for API |
| Docker (optional) | Recent | For full-stack in one command |

---

## 1. Clone and install dependencies

```bash
git clone <repo-url> Assumption-Sniper
cd Assumption-Sniper
pnpm install
```

---

## 2. Environment variables

Copy the example file and edit values:

```bash
cp .env.example .env
```

### Required for local development

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Async Postgres connection | `postgresql+asyncpg://postgres:postgres@localhost:5432/assumption_sniper` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `OPENROUTER_API_KEY` | OpenRouter API key | Your key from openrouter.ai |
| `JWT_SECRET` | Token signing secret | Long random string |

### Commonly adjusted

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENROUTER_PRIMARY_MODEL` | `openai/gpt-4o-mini` | Default model |
| `ROUTING_PROFILE` | `balanced` | `cost`, `balanced`, or `quality` |
| `BETA_ENABLED` | `false` | Enable invite-code beta |
| `BETA_INVITE_CODES` | `founder-beta,pm-beta` | Valid invite codes when beta on |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Web → API URL |

Full list: [.env.example](../.env.example)

---

## 3. Option A — Docker (recommended)

Runs API, web, Postgres, and Redis together.

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Web | http://localhost:3000 |
| API | http://localhost:8000 |
| Health | http://localhost:8000/api/v1/health |

Schema migrations run automatically when the API container starts.

---

## 4. Option B — Local processes

### Start Postgres and Redis

Ensure both are running and match your `.env` URLs.

### Initialize the database (first time only)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r apps/api/requirements.txt -r apps/api/requirements-dev.txt
python -m apps.api.scripts.init_db
```

### Start the API

```bash
python -m uvicorn app.main:app --reload --app-dir apps/api
```

### Start the web app (separate terminal)

```bash
pnpm -C apps/web dev
```

---

## 5. First-run walkthrough

1. Open http://localhost:3000
2. Register at `/login` (or use demo at `/demo`)
3. Submit an idea from `/app`
4. Watch run progress stream; open the run detail page for results

---

## 6. Development commands

| Task | Command |
|------|---------|
| API tests | `pytest -q apps/api` |
| Web tests | `pnpm -C apps/web test` |
| Web e2e | `pnpm -C apps/web test:e2e` |
| Lint API | `ruff check apps/api` |
| Format API | `ruff format apps/api` |
| Lint web | `pnpm -C apps/web lint` |
| Typecheck web | `pnpm -C apps/web typecheck` |
| Smoke test | `python apps/api/scripts/smoke_test.py --url http://localhost:8000` |
| Exit criteria | `python apps/api/scripts/verify_exit_criteria.py` |
| Load baseline | `python apps/api/scripts/load_test.py --url http://localhost:8000` |

Pre-commit: `pre-commit install` (uses `.pre-commit-config.yaml`)

---

## 7. Staging and production

| Environment | Trigger | Config |
|-------------|---------|--------|
| Staging | Merge to `main` | `deploy/env/staging.env.example` |
| Production | Manual CD workflow | `deploy/env/production.env.example` |

Deploy scripts: `deploy/deploy.sh`, `deploy/rollback.sh`

Guides: [deploy/infrastructure.md](deploy/infrastructure.md), [deploy/launch-checklist.md](deploy/launch-checklist.md)

---

## 8. Troubleshooting

### API won't start — database connection error

- Confirm Postgres is running and `DATABASE_URL` is correct
- Run `python -m apps.api.scripts.init_db` if schema is missing

### Web shows API errors

- Check `NEXT_PUBLIC_API_BASE_URL` points to the running API
- Verify CORS: API allows the web origin in development

### Runs stay queued

- Confirm Redis is running and `REDIS_URL` is reachable
- Check `MAX_QUEUE_DEPTH` and user concurrency limits in `.env`

### OpenRouter / AI failures

- Set a valid `OPENROUTER_API_KEY`
- Check circuit breaker cooldown (`OPENROUTER_CIRCUIT_*` vars)
- Try `ROUTING_PROFILE=cost` to reduce model load

### Tests fail locally

```bash
# API tests use mocked Redis/DB in most cases; ensure env is set:
set DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/test
set REDIS_URL=redis://localhost:6379/0
set OPENROUTER_API_KEY=test-key
set JWT_SECRET=test-secret-for-pytest
pytest -q apps/api
```

---

## 9. Where to go next

| Topic | Document |
|-------|----------|
| API contracts & pipeline | [architecture.md](architecture.md) |
| All documentation | [index.md](index.md) |
| Production readiness | [project-complete.md](project-complete.md) |
| Contributing | [../CONTRIBUTING.md](../CONTRIBUTING.md) |
