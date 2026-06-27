# Runbook: Budget burn / cost spike

## Symptoms

- `BudgetBurnHigh` alert
- Rapid increase in `ai_cost_usd_total` or `budget_usd_hourly_total`
- Usage records showing abnormal token volume

## Investigation

1. Grafana panel: AI Cost USD / min by task.
2. Check top users via usage API and audit logs (`run.start` volume).
3. Identify cache miss spike vs. genuine traffic increase.
4. Review concurrent run queue depth.

## Mitigation

1. Lower `RUN_CREATION_PER_HOUR` and `MAX_CONCURRENT_RUNS_PER_USER`.
2. Run cache warming for common prompts: `python apps/api/scripts/warm_cache.py --execute`.
3. Temporarily disable expensive stages via feature flags if enabled.
4. Contact heavy users if abuse suspected.

## Escalation

If hourly spend exceeds 2× budget threshold, page primary on-call and notify product lead.
