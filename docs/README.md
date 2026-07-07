# Documentation index

Central index for Assumption Sniper v1. Start with [getting-started.md](getting-started.md), then use the sections below by role.

## Getting started

| Document | Description |
|----------|-------------|
| [getting-started.md](getting-started.md) | Local dev, Docker, tests, environment |
| [architecture.md](architecture.md) | API contracts, data model, pipeline stages |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | Branch workflow, lint, and review |

## Deployment

| Document | Description |
|----------|-------------|
| [deploy/infrastructure.md](deploy/infrastructure.md) | Staging and production topology |
| [deploy/launch-checklist.md](deploy/launch-checklist.md) | Pre-launch checklist |
| [deploy/canary-blue-green.md](deploy/canary-blue-green.md) | Blue/green deployment |
| [deploy/rollback.md](deploy/rollback.md) | Rollback procedure |
| [../deploy/deploy.sh](../deploy/deploy.sh) | Deploy script |
| [../deploy/rollback.sh](../deploy/rollback.sh) | Rollback script |

## Release (v1)

| Document | Description |
|----------|-------------|
| [release/v1.0.0.md](release/v1.0.0.md) | Release notes |
| [release/sign-off.md](release/sign-off.md) | Owner sign-off |
| [release/eval-thresholds.json](release/eval-thresholds.json) | Eval quality gates |
| [release/exit-criteria-report.json](release/exit-criteria-report.json) | Automated gate report (generated) |

## Security

| Document | Description |
|----------|-------------|
| [security/permissions.md](security/permissions.md) | Auth model and least privilege |
| [security/review-report.md](security/review-report.md) | v1 security review |

## Observability

| Document | Description |
|----------|-------------|
| [observability/slo-definitions.md](observability/slo-definitions.md) | SLOs and error budgets |
| [observability/perf-baseline.json](observability/perf-baseline.json) | Load-test p95 baseline |
| [observability/prometheus-alerts.yml](observability/prometheus-alerts.yml) | Alert rules |
| [observability/grafana-dashboard.json](observability/grafana-dashboard.json) | Grafana dashboard |

## Operations

| Document | Description |
|----------|-------------|
| [operations/backup-restore.md](operations/backup-restore.md) | Backup and restore |
| [operations/drill-log.md](operations/drill-log.md) | Incident drill log |
| [operations/runbooks/pipeline-failures.md](operations/runbooks/pipeline-failures.md) | Pipeline failures |
| [operations/runbooks/high-error-rate.md](operations/runbooks/high-error-rate.md) | High API error rate |
| [operations/runbooks/budget-burn.md](operations/runbooks/budget-burn.md) | Budget burn |
| [operations/runbooks/redis-db-outage.md](operations/runbooks/redis-db-outage.md) | Redis/Postgres outage |
| [on-call/escalation.md](on-call/escalation.md) | Escalation path |
| [on-call/rotation.json](on-call/rotation.json) | On-call rotation |

## Product

| Document | Description |
|----------|-------------|
| [beta/program.md](beta/program.md) | Private beta program |
| [product/roadmap-v2.md](product/roadmap-v2.md) | Post-v1 roadmap |
| [metrics/monthly-snapshot.json](metrics/monthly-snapshot.json) | Monthly success metrics |

## Scripts

| Script | Purpose |
|--------|---------|
| `apps/api/scripts/verify_exit_criteria.py` | Run all v1 exit criteria |
| `apps/api/scripts/backup_restore_test.py` | Backup/restore validation |
| `apps/api/scripts/smoke_test.py` | Post-deploy smoke tests |
| `apps/api/scripts/load_test.py` | Regenerate perf baseline |

## Project planning

| Document | Description |
|----------|-------------|
| [../PLAN.md](../PLAN.md) | Delivery phases (1–17) |
| [../PRD.md](../PRD.md) | Product requirements |
