# Incident response drill log

Record tabletop and live drills here. Each entry should include participants, scenario, actions taken, gaps, and follow-ups.

---

## Drill 2026-06-16 — Pipeline failure + on-call escalation

**Status: completed**  
**Type:** Tabletop + staging smoke validation  
**Duration:** 45 minutes  
**Participants:** Engineering lead, on-call primary, product owner

### Scenario

1. Prometheus alert `PipelineStageFailures` fires — skeptic stage error rate > 5%.
2. On-call acknowledges within 5 minutes and opens incident channel.
3. Engineer follows `docs/operations/runbooks/pipeline-failures.md` — checks AI circuit breaker, Redis queue depth, recent deploys.
4. Simulated root cause: OpenRouter rate limit; mitigation: enable cost routing profile and pause non-critical runs.
5. Escalation path exercised per `docs/on-call/escalation.md` when staging recovery exceeded 15 minutes (simulated).

### Actions validated

- Runbook steps are actionable without tribal knowledge
- Grafana dashboard links resolve from alert annotations
- Rollback script (`deploy/rollback.sh`) tested in staging
- Smoke tests (`apps/api/scripts/smoke_test.py`) pass post-recovery

### Gaps and follow-ups

| Gap | Owner | Due |
|-----|-------|-----|
| Add OpenRouter rate-limit runbook section | Engineering | v1.0.1 |
| Automate paging test in quarterly drill | On-call | Q3 2026 |

**Drill outcome:** Pass — team can execute incident response for pipeline and API outages.

---

## Next drill (scheduled)

**Target:** 2026-09-16  
**Scenario:** Redis/Postgres outage (`docs/operations/runbooks/redis-db-outage.md`)
