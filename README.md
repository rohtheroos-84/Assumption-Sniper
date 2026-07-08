# Assumption Sniper

AI that finds the flaws in your thinking before reality does.

Assumption Sniper decomposes ideas into assumptions, stress-tests them with multi-agent critiques, simulates edge cases, scores risk, and reconstructs stronger versions — with a web dashboard for graphs, heatmaps, and comparisons.

**Status:** v1.0.0 production ready — [project-complete.md](docs/project-complete.md)

---

## Quick start

```bash
pnpm install
cp .env.example .env    # set OPENROUTER_API_KEY, JWT_SECRET, DATABASE_URL, REDIS_URL

docker compose up --build
```

| Service | URL |
|---------|-----|
| Web | http://localhost:3000 |
| API | http://localhost:8000 |
| Health | http://localhost:8000/api/v1/health |

**Full setup:** [docs/getting-started.md](docs/getting-started.md)

---

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/index.md](docs/index.md) | **Master index** — navigate all docs by role and topic |
| [docs/getting-started.md](docs/getting-started.md) | Prerequisites, env vars, Docker/local, troubleshooting |
| [docs/project-complete.md](docs/project-complete.md) | Delivery summary, exit criteria, test status |
| [docs/architecture.md](docs/architecture.md) | API contracts and pipeline design |
| [PLAN.md](PLAN.md) | 17 delivery phases (complete) |
| [PRD.md](PRD.md) | Product requirements |

---

## Repository layout

```
apps/api/          FastAPI backend, pipeline, AI, tests
apps/web/          Next.js frontend
deploy/            Deploy scripts and env templates
docs/              All documentation (start at docs/index.md)
.github/workflows  CI and CD
```

---

## Development

```bash
pytest -q apps/api
pnpm -C apps/web test
```

Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Production

```bash
python apps/api/scripts/verify_exit_criteria.py
```

Launch: [docs/deploy/launch-checklist.md](docs/deploy/launch-checklist.md) | Release notes: [docs/release/v1.0.0.md](docs/release/v1.0.0.md)
