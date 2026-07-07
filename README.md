# Assumption Sniper

AI that finds the flaws in your thinking before reality does.

Assumption Sniper is a cognitive debugging platform: submit an idea, and the system decomposes it into assumptions, attacks weak logic with multi-agent skeptic critiques, simulates edge cases, scores risk, and reconstructs a stronger version. Results appear in a web dashboard with graphs, heatmaps, and side-by-side reconstruction.

**Status:** v1.0.0 production ready (see `docs/release/v1.0.0.md`).

## Quick start

```bash
# clone and install
pnpm install
cp .env.example .env   # fill DATABASE_URL, REDIS_URL, OPENROUTER_API_KEY, JWT_SECRET

# option A: docker (recommended)
docker compose up --build

# option B: local processes
python -m apps.api.scripts.init_db
python -m uvicorn app.main:app --reload --app-dir apps/api
pnpm -C apps/web dev
```

- Web: http://localhost:3000  
- API: http://localhost:8000  
- Health: http://localhost:8000/api/v1/health  

Full setup: [docs/getting-started.md](docs/getting-started.md)

## Core workflow

1. User submits an idea (text).
2. Pipeline decomposes goals, dependencies, and assumptions.
3. Skeptic agents critique weak logic.
4. Edge cases are simulated and scored.
5. Reconstruction proposes a more viable version.
6. Dashboard visualizes assumptions, risk, critiques, and output.

## Repository layout

```
Assumption-Sniper/
├── apps/
│   ├── api/          # FastAPI backend, pipeline, AI layer, tests
│   └── web/          # Next.js frontend (landing, app, demo, beta)
├── deploy/           # Deploy/rollback scripts and env templates
├── docs/             # Architecture, ops, security, release docs (see docs/README.md)
├── .github/workflows # CI and CD
├── docker-compose.yml
├── PLAN.md           # Delivery phases (1–17 complete)
└── PRD.md            # Product requirements
```

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js, React, Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| Data | PostgreSQL, Redis |
| AI | OpenRouter (role-specific prompts, routing profiles) |
| Ops | Docker, Prometheus metrics, Grafana dashboards |

## Development

```bash
pytest -q apps/api
pnpm -C apps/web test
ruff check apps/api
pnpm -C apps/web lint
```

Pre-commit hooks: `.pre-commit-config.yaml`

Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)

## Production readiness

Exit criteria (phase 17) are enforced by:

```bash
python apps/api/scripts/backup_restore_test.py --schema-only
python apps/api/scripts/verify_exit_criteria.py
```

| Area | Location |
|------|----------|
| Launch checklist | `docs/deploy/launch-checklist.md` |
| SLOs and latency baseline | `docs/observability/` |
| Runbooks and drills | `docs/operations/` |
| Security review | `docs/security/review-report.md` |
| Release notes and sign-off | `docs/release/` |
| Doc index | `docs/README.md` |

## Deployment

- **CI:** lint, test, security scans on every PR (`ci.yml`)
- **CD:** build images, staging deploy, production with approval (`cd.yml`)
- **Compose:** `docker-compose.staging.yml`, `docker-compose.production.yml`
- **Rollback:** `deploy/rollback.sh`

## License

See repository license file if present; otherwise treat as private until published.
