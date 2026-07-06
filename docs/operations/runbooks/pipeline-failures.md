# Runbook: Pipeline stage failures

## Symptoms

- `PipelineStageFailures` alert firing
- Runs stuck in `failed` status
- SSE events show `stage_failed`

## Investigation

1. Find the failing run id from audit logs or user report.
2. Fetch the trace: `GET /api/v1/ops/traces/{run_id}` (authenticated owner).
3. Check run events: `GET /api/v1/runs/{run_id}/events`.
4. Review structured logs filtered by `run_id` and `trace_id`.

## Common causes

| Stage | Likely cause | Fix |
|-------|--------------|-----|
| decomposition | OpenRouter timeout | Retry run; check circuit breaker |
| assumptions | Schema validation failure | Inspect prompt regression tests |
| critique/simulation | Model overload | Fallback model should engage; verify routing flags |
| reconstruction | Empty upstream data | Re-run prior stages |

## Mitigation

1. Cancel stuck runs: `POST /api/v1/runs/{run_id}/cancel`.
2. Retry: `POST /api/v1/runs/{run_id}/retry`.
3. If OpenRouter circuit is open, wait for cooldown or reduce concurrency.

## Escalation

If failure rate > 20% for 30 minutes, page on-call primary (see `docs/on-call/escalation.md`).
