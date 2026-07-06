# Runbook: Redis or database outage

## Symptoms

- `/api/v1/ready` returns `ready: false`
- Rate limiting errors or 503s across endpoints
- Queue enqueue failures (429 with queue errors)

## Investigation

1. Hit `/api/v1/ready` and note `db` / `redis` flags.
2. Verify managed service status pages.
3. Check connection strings and network policies.

## Mitigation

| Component | Action |
|-----------|--------|
| Redis | Failover to replica; restart service; verify `REDIS_URL` |
| Postgres | Failover primary; verify pool settings; run `SELECT 1` |

API can serve read-only health/ping without full functionality, but runs and AI routes require both services.

## Escalation

Page infrastructure on-call immediately for production outages > 5 minutes.
