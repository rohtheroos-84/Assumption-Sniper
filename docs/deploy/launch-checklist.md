# Production launch checklist

Complete all items before approving the first production release. Sign off in the PR or release ticket.

## Infrastructure

- [ ] Managed Postgres provisioned with backups enabled
- [ ] Managed Redis provisioned with TLS and auth
- [ ] Staging environment mirrors production topology
- [ ] Secrets stored in vault / GitHub environment secrets (not in git)
- [ ] DNS and TLS certificates configured for API and web domains

## Deployment pipeline

- [ ] CI passes on `main` (web, api, security scans)
- [ ] CD workflow builds and pushes container images
- [ ] Staging auto-deploy succeeds after merge to `main`
- [ ] Staging smoke tests pass (`smoke_test.py`)
- [ ] Migration runs automatically on API container start
- [ ] Blue/green slots configured for production
- [ ] Rollback script tested in staging

## Quality gates

- [ ] All API tests pass locally and in CI (105+)
- [ ] E2E workflow tests pass in CI
- [ ] p95 latency baseline recorded (`docs/perf-baseline.json`)
- [ ] Security review complete (Phase 13)
- [ ] Observability dashboards imported (`docs/observability/grafana-dashboard.json`)
- [ ] Alert rules loaded (`docs/observability/prometheus-alerts.yml`)

## Operational readiness

- [ ] Runbooks reviewed (`docs/runbooks/`)
- [ ] On-call rotation configured (`docs/on-call/rotation.json`)
- [ ] Escalation path documented (`docs/on-call/escalation.md`)
- [ ] Data retention purge job scheduled (`scripts/purge_retention.py`)

## Launch approval

| Role | Name | Date | Approved |
|------|------|------|----------|
| Engineering lead | | | [ ] |
| Product owner | | | [ ] |
| On-call primary | | | [ ] |

## Post-launch (first 24h)

- [ ] Monitor error rate and latency dashboards
- [ ] Verify smoke tests on production URL
- [ ] Confirm budget burn within threshold
- [ ] Triage any user-reported issues

**Launch approved:** _______________  **Date:** _______________
