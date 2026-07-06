# Backup and restore

Procedures for PostgreSQL (primary datastore) and Redis (cache/queue).

## PostgreSQL

### Backup (managed)

Production uses managed Postgres with automated daily snapshots and point-in-time recovery. Confirm in your cloud provider console before launch.

### Backup (manual)

```bash
pg_dump "$DATABASE_URL" --format=custom --file=assumption-sniper-$(date +%Y%m%d).dump
```

Store dumps in encrypted object storage with 30-day retention.

### Restore

```bash
pg_restore --clean --if-exists --dbname="$DATABASE_URL" assumption-sniper-YYYYMMDD.dump
python apps/api/scripts/migrate.py
python apps/api/scripts/smoke_test.py --url "$API_BASE_URL"
```

## Redis

Redis holds ephemeral queue and cache data. No restore is required for v1 — rebuild from Postgres on cold start. Enable AOF/RDB only if you introduce durable queue semantics.

## Validation

Run the automated backup/restore test after schema changes:

```bash
python apps/api/scripts/backup_restore_test.py
# or without a live database:
python apps/api/scripts/backup_restore_test.py --schema-only
```

Results are recorded in `docs/operations/backup-restore-test-record.json`.

## RTO / RPO targets (v1)

| Metric | Target |
|--------|--------|
| RPO (Postgres) | ≤ 24 hours (daily backup) |
| RTO (API + web) | ≤ 2 hours (redeploy + restore) |

See `docs/operations/runbooks/redis-db-outage.md` for incident steps.
