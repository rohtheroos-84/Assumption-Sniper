# Documentation index

Navigation hub for **Assumption Sniper v1.0.0**. Use this page to find what each document covers and who should read it.

**New here?** Start with [getting-started.md](getting-started.md), then [project-complete.md](project-complete.md) for the full delivery summary.

---

## Quick links by role

| Role | Start here |
|------|------------|
| Developer | [getting-started.md](getting-started.md) → [architecture.md](architecture.md) |
| DevOps / SRE | [deploy/infrastructure.md](deploy/infrastructure.md) → [operations/](operations/) |
| On-call | [on-call/escalation.md](on-call/escalation.md) → [operations/runbooks/](operations/runbooks/) |
| Product / PM | [../PRD.md](../PRD.md) → [product/roadmap-v2.md](product/roadmap-v2.md) |
| Security | [security/permissions.md](security/permissions.md) → [security/review-report.md](security/review-report.md) |
| Release manager | [release/v1.0.0.md](release/v1.0.0.md) → [deploy/launch-checklist.md](deploy/launch-checklist.md) |

---

## Project overview

| Document | What it says |
|----------|--------------|
| [project-complete.md](project-complete.md) | **Project done summary** — all 17 phases complete, what was built, how to verify, repo map |
| [../README.md](../README.md) | Repository landing page: tagline, quick start, stack, links |
| [../PRD.md](../PRD.md) | Product requirements: vision, users, features, success metrics |
| [../PLAN.md](../PLAN.md) | Delivery plan with 17 phases (all checked off) |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | Branch workflow, commit style, lint/test before PR |

---

## Setup and development

| Document | What it says |
|----------|--------------|
| [getting-started.md](getting-started.md) | **Full setup guide** — prerequisites, env vars, Docker vs local, DB init, tests, troubleshooting |
| [architecture.md](architecture.md) | API request/response shapes, pipeline stages, data model, endpoints |
| [../.env.example](../.env.example) | All environment variables with defaults |
| [../apps/web/README.md](../apps/web/README.md) | Web app-only quick start |

---

## Release and production gate

| Document | What it says |
|----------|--------------|
| [release/v1.0.0.md](release/v1.0.0.md) | v1.0.0 release notes: features, API surface, known limits |
| [release/sign-off.md](release/sign-off.md) | Owner sign-off for production release |
| [release/eval-thresholds.json](release/eval-thresholds.json) | Eval quality gate thresholds (pass rate, relevance, themes) |
| [release/exit-criteria-report.json](release/exit-criteria-report.json) | **Generated** — last automated exit-criteria run (8 gates) |

**Verify gates:** `python apps/api/scripts/verify_exit_criteria.py`

---

## Deployment

| Document | What it says |
|----------|--------------|
| [deploy/infrastructure.md](deploy/infrastructure.md) | Staging/production topology, managed services, networking |
| [deploy/launch-checklist.md](deploy/launch-checklist.md) | Pre-launch checklist: infra, CI/CD, quality, ops approval |
| [deploy/canary-blue-green.md](deploy/canary-blue-green.md) | Blue/green slot strategy and traffic cutover |
| [deploy/rollback.md](deploy/rollback.md) | Rollback steps after a bad deploy |
| [../deploy/deploy.sh](../deploy/deploy.sh) | Deploy script (staging/production) |
| [../deploy/rollback.sh](../deploy/rollback.sh) | Rollback script |
| [../deploy/env/](../deploy/env/) | Environment templates (`development`, `staging`, `production`) |
| [../docker-compose.yml](../docker-compose.yml) | Local full stack |
| [../docker-compose.staging.yml](../docker-compose.staging.yml) | Staging compose overlay |
| [../docker-compose.production.yml](../docker-compose.production.yml) | Production compose overlay |
| [../.github/workflows/ci.yml](../.github/workflows/ci.yml) | CI: lint, test, security, Docker, exit criteria |
| [../.github/workflows/cd.yml](../.github/workflows/cd.yml) | CD: build images, deploy staging/production |

---

## Security

| Document | What it says |
|----------|--------------|
| [security/permissions.md](security/permissions.md) | Auth surfaces, project scoping, API keys, audit actions, retention |
| [security/review-report.md](security/review-report.md) | v1 security review: bandit/pip-audit/Trivy results, approved status |

---

## Observability

| Document | What it says |
|----------|--------------|
| [observability/slo-definitions.md](observability/slo-definitions.md) | SLOs: availability, p95 latency, pipeline success, AI errors, budget |
| [observability/perf-baseline.json](observability/perf-baseline.json) | Load-test p95 baseline for health/ping endpoints |
| [observability/prometheus-alerts.yml](observability/prometheus-alerts.yml) | Prometheus alert rule definitions |
| [observability/grafana-dashboard.json](observability/grafana-dashboard.json) | Grafana dashboard import JSON |

**Metrics endpoint:** `GET /api/v1/metrics`

---

## Operations

| Document | What it says |
|----------|--------------|
| [operations/backup-restore.md](operations/backup-restore.md) | Postgres backup/restore commands, RTO/RPO targets |
| [operations/backup-restore-test-record.json](operations/backup-restore-test-record.json) | **Generated** — last backup/restore validation result |
| [operations/drill-log.md](operations/drill-log.md) | Incident response drill history and outcomes |
| [operations/runbooks/pipeline-failures.md](operations/runbooks/pipeline-failures.md) | Pipeline stage failures: circuit breaker, queue, AI errors |
| [operations/runbooks/high-error-rate.md](operations/runbooks/high-error-rate.md) | High API 5xx rate: logs, deploy rollback, dependency checks |
| [operations/runbooks/budget-burn.md](operations/runbooks/budget-burn.md) | AI budget burn spike: routing profile, rate limits |
| [operations/runbooks/redis-db-outage.md](operations/runbooks/redis-db-outage.md) | Redis or Postgres outage: failover, restore, smoke tests |
| [on-call/escalation.md](on-call/escalation.md) | Escalation tiers and contact path |
| [on-call/rotation.json](on-call/rotation.json) | On-call rotation schedule (JSON) |

---

## Product and growth

| Document | What it says |
|----------|--------------|
| [beta/program.md](beta/program.md) | Private beta: invite codes, feedback loop, success criteria |
| [product/roadmap-v2.md](product/roadmap-v2.md) | Post-v1 feature roadmap |
| [metrics/monthly-snapshot.json](metrics/monthly-snapshot.json) | Monthly success metrics snapshot template |

---

## Scripts reference

| Script | What it does |
|--------|--------------|
| `apps/api/scripts/init_db.py` | Create database schema (first run) |
| `apps/api/scripts/migrate.py` | Apply schema migrations on deploy |
| `apps/api/scripts/smoke_test.py` | Post-deploy health and API smoke tests |
| `apps/api/scripts/verify_exit_criteria.py` | Run all 8 production exit criteria |
| `apps/api/scripts/backup_restore_test.py` | Validate backup/restore cycle |
| `apps/api/scripts/load_test.py` | Regenerate `observability/perf-baseline.json` |
| `apps/api/scripts/purge_retention.py` | Purge data per retention policy |
| `apps/api/scripts/warm_cache.py` | Warm AI response cache |
| `apps/api/eval/tune_from_eval.py` | Eval-based prompt/scoring recommendations |

---

## Repository layout

```
Assumption-Sniper/
├── apps/
│   ├── api/                 # FastAPI, pipeline, AI, tests, scripts
│   └── web/                 # Next.js UI (landing, app, demo, beta)
├── deploy/                  # Deploy scripts and env templates
├── docs/                    # All documentation (this index)
│   ├── index.md             # ← you are here
│   ├── getting-started.md
│   ├── project-complete.md
│   ├── architecture.md
│   ├── deploy/
│   ├── observability/
│   ├── operations/
│   ├── release/
│   ├── security/
│   ├── on-call/
│   ├── beta/
│   ├── product/
│   └── metrics/
├── .github/workflows/       # CI and CD
├── docker-compose*.yml
├── PLAN.md
├── PRD.md
└── README.md
```

---

## Document count

| Area | Files |
|------|-------|
| Setup & architecture | 2 |
| Release | 4 (+ 1 generated) |
| Deploy | 4 |
| Security | 2 |
| Observability | 4 |
| Operations | 6 (+ 1 generated) |
| On-call | 2 |
| Product | 3 |

**Total curated docs:** 27 markdown/JSON guides (+ 2 generated records).
