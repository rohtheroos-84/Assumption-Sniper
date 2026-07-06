# Runbook: High API error rate

## Symptoms

- `HighApiErrorRate` alert
- Elevated 5xx responses in Grafana
- User reports of failed requests

## Investigation

1. Check `/api/v1/ready` for database and Redis health.
2. Inspect recent deploys and rollback if correlated.
3. Query logs for `status_code=500` with recent `trace_id` values.
4. Review `errors_total` by component in Prometheus.

## Common causes

- Database connection pool exhaustion → increase `DB_POOL_SIZE` or scale DB.
- Redis unavailable → rate limiting and queue/backpressure fail; restore Redis first.
- Unhandled exceptions in new routes → check Sentry/logs stack traces.

## Mitigation

1. Scale API replicas if CPU-saturated.
2. Temporarily reduce `MAX_CONCURRENT_RUNS_PER_USER` to shed load.
3. Roll back to last known good release if deploy-related.

## Escalation

Page platform on-call if error rate remains > 2% for 15 minutes after mitigation.
