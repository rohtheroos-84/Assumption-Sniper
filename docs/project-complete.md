# Project complete — Assumption Sniper v1.0.0

This document is the final delivery summary. All work in [PLAN.md](../PLAN.md) (phases 0–17) is complete.

---

## What was built

**Assumption Sniper** is a cognitive debugging platform. Users submit an idea; the system:

1. Decomposes it into assumptions and dependencies
2. Runs multi-agent skeptic critiques
3. Simulates edge cases and scores risk
4. Reconstructs a stronger version of the idea
5. Presents results in a web dashboard

### Applications

| App | Path | Purpose |
|-----|------|---------|
| API | `apps/api/` | FastAPI backend, AI pipeline, auth, metrics |
| Web | `apps/web/` | Next.js UI: landing (`/`), app (`/app`), demo (`/demo`), beta (`/beta`) |

### Infrastructure

- **PostgreSQL** — persistent data (users, runs, assumptions, critiques, etc.)
- **Redis** — queue, cache, circuit breaker state, tracing
- **OpenRouter** — LLM calls with cost/quality/balanced routing profiles
- **Docker** — API and web images; compose for dev/staging/production

---

## Delivery phases (summary)

| Phase | Focus | Status |
|-------|-------|--------|
| 0 | Alignment, scope, success metrics | Done |
| 1 | Repo, dev environment, CI | Done |
| 2 | Architecture and data design | Done |
| 3–4 | API foundation, auth | Done |
| 5–7 | AI layer, pipeline, streaming | Done |
| 8–10 | Web UI, visualization, polish | Done |
| 11 | Quality: tests, evals, e2e | Done |
| 12 | Performance: queue, cache, load tests | Done |
| 13 | Security: sanitization, audit, retention | Done |
| 14 | Observability: metrics, alerts, runbooks | Done |
| 15 | Deployment: Docker, CD, smoke tests | Done |
| 16 | Launch: landing, beta, analytics, routing | Done |
| 17 | Production exit criteria | Done |

Full checklist: [PLAN.md](../PLAN.md)

---

## Production exit criteria (phase 17)

All eight gates pass. Re-verify anytime:

```bash
python apps/api/scripts/backup_restore_test.py --schema-only
python apps/api/scripts/verify_exit_criteria.py
```

| Gate | Evidence |
|------|----------|
| p95 latency & error budgets | `docs/observability/perf-baseline.json`, SLOs in `slo-definitions.md` |
| Eval quality | `docs/release/eval-thresholds.json` — 3/3 cases pass |
| Security review | `docs/security/review-report.md` — approved, 0 critical |
| Backup & restore | `docs/operations/backup-restore-test-record.json` |
| Incident drills | `docs/operations/drill-log.md` |
| Docs & runbooks | `docs/index.md` (this tree) |
| Release notes | `docs/release/v1.0.0.md` |
| Owner sign-off | `docs/release/sign-off.md` |

Latest report: [release/exit-criteria-report.json](release/exit-criteria-report.json)

---

## Test coverage

| Suite | Command | Status |
|-------|---------|--------|
| API unit/integration | `pytest -q apps/api` | 118+ tests |
| Web unit | `pnpm -C apps/web test` | Vitest |
| Web e2e | `pnpm -C apps/web test:e2e` | Playwright |
| CI | `.github/workflows/ci.yml` | Lint, test, security, Docker, exit criteria |

---

## How to run locally

**Fastest path (Docker):**

```bash
cp .env.example .env
# Set OPENROUTER_API_KEY and JWT_SECRET at minimum
docker compose up --build
```

- Web: http://localhost:3000
- API: http://localhost:8000
- Health: http://localhost:8000/api/v1/health

**Without Docker:** see [getting-started.md](getting-started.md).

---

## How to deploy

1. Complete [deploy/launch-checklist.md](deploy/launch-checklist.md)
2. Configure secrets from `deploy/env/production.env.example`
3. Run CD workflow or `deploy/deploy.sh`
4. Run `python apps/api/scripts/smoke_test.py --url <production-url>`
5. Import observability assets from `docs/observability/`

Details: [deploy/infrastructure.md](deploy/infrastructure.md)

---

## Key API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Get JWT |
| POST | `/api/v1/runs` | Start analysis run |
| GET | `/api/v1/runs/{id}` | Run status and results |
| GET | `/api/v1/runs/{id}/events` | SSE progress stream |
| GET | `/api/v1/metrics` | Prometheus metrics |

Full contracts: [architecture.md](architecture.md)

---

## v1 scope boundaries

**Included:** text input, assumption extraction, skeptic analysis, edge-case simulation, reconstruction, dashboard, auth, API keys, beta program, demo mode.

**Excluded (v2+):** SSO, team collaboration, web-search validation, historical startup analysis. See [product/roadmap-v2.md](product/roadmap-v2.md).

---

## Documentation map

All docs are indexed in [index.md](index.md). No images are required — everything is text and JSON/YAML configs.

---

## Next steps after v1

1. Tag `v1.0.0` and publish [release/v1.0.0.md](release/v1.0.0.md) to GitHub Releases
2. Execute production deploy per launch checklist
3. Monitor first 24h (error rate, latency, budget burn)
4. Iterate from [product/roadmap-v2.md](product/roadmap-v2.md) and monthly metrics

**Project status: complete and production ready.**
