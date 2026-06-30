# Rollback plan

## When to rollback

- Smoke tests fail after deploy
- Error rate exceeds SLO for 10+ minutes post-deploy
- p95 latency doubles vs. baseline
- Critical functional regression reported

## Staging rollback

```bash
# Revert to previous image tag (default tag: previous)
./deploy/rollback.sh staging previous

# Or redeploy last known good commit via GitHub Actions "Re-run job"
```

**RTO target:** 15 minutes  
**RPO target:** No data loss (migrations are forward-only schema sync)

## Production rollback

Production uses blue/green — rollback means **switching traffic back** to the previous slot without redeploying:

```bash
./deploy/rollback.sh production previous
```

This:

1. Sets `TRAFFIC_SLOT` to the previously active slot.
2. Optionally pins images to the `previous` tag.
3. Runs smoke tests against `PRODUCTION_API_URL`.

## Database migrations

Migrations run via `scripts/migrate.py` (SQLAlchemy `create_all`) at container start. They are additive and idempotent.

- **Rollback does not reverse schema changes.** If a deploy introduced breaking schema changes, restore from backup instead.
- Test migrations in staging before production deploy.

## Verification after rollback

- [ ] `./apps/api/scripts/smoke_test.py --url $API_URL` passes
- [ ] `/api/v1/ready` returns `ready: true`
- [ ] Grafana error rate returns to baseline within 15 minutes
- [ ] No elevated pipeline failure alerts

## Emergency contacts

See `docs/on-call/escalation.md` for severity levels and escalation path.
