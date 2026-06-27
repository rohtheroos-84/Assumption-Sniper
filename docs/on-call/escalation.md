# On-call escalation

## Severity levels

| Severity | Examples | Response time | Channel |
|----------|----------|---------------|---------|
| S1 | API down, data loss risk | 15 minutes | PagerDuty page + Slack |
| S2 | Pipeline failure spike, budget burn | 30 minutes | PagerDuty page |
| S3 | Elevated latency, non-critical errors | 4 hours | Slack ticket |
| S4 | Informational | Next business day | Slack |

## Escalation path

1. **Primary on-call** — first responder (see `rotation.json`).
2. **Secondary on-call** — engaged if primary does not ack within 15 minutes (S1/S2) or 30 minutes (S3).
3. **Engineering lead** — engaged for S1 lasting > 1 hour or any customer-data incident.
4. **Product lead** — engaged for sustained outage > 2 hours or budget overrun > 3× threshold.

## Alert routing

Prometheus alerts in `docs/observability/prometheus-alerts.yml` map to PagerDuty via Alertmanager:

- `severity: page` → primary on-call
- `severity: ticket` → Slack `#assumption-sniper-alerts` with 30-minute reminder

## Handoff checklist

- Review open incidents and recent deploys
- Confirm Grafana dashboard and `/api/v1/metrics` scrape health
- Verify runbook links in alert annotations resolve
- Acknowledge pending PagerDuty shifts

## Useful commands

```bash
# Check readiness
curl -s http://localhost:8000/api/v1/ready | jq

# Inspect SLO targets
curl -s http://localhost:8000/api/v1/ops/slo | jq

# View Prometheus metrics
curl -s http://localhost:8000/api/v1/metrics | head
```
