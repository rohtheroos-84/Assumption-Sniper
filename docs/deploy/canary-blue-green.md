# Blue/green and canary deployments

## Strategy

Production uses **blue/green** slots (`api-blue` / `api-green`, `web-blue` / `web-green`). Only one slot receives 100% traffic at a time, controlled by `TRAFFIC_SLOT`.

Optional **canary** releases route a percentage of traffic to the inactive slot before full promotion.

## Deploy flow

```bash
# Staging (auto on merge to main via CD workflow)
./deploy/deploy.sh staging

# Production — full cutover to inactive slot
./deploy/deploy.sh production 0

# Production — 10% canary to new slot first
./deploy/deploy.sh production 10
```

## Steps (production)

1. Identify active slot (`TRAFFIC_SLOT`, default `blue`).
2. Deploy new images to the **inactive** slot.
3. Run smoke tests against the inactive slot URL (internal LB or direct).
4. If canary percent > 0, shift partial traffic via load balancer weights.
5. Monitor error rate, p95 latency, and budget burn for 15–30 minutes.
6. Promote to 100% or run `./deploy/rollback.sh production`.

## Load balancer configuration

Configure your ingress/LB to route by slot label:

| Variable | Purpose |
|----------|---------|
| `TRAFFIC_SLOT` | Slot receiving 100% traffic (`blue` or `green`) |
| `CANARY_SLOT` | Slot receiving canary traffic |
| `CANARY_PERCENT` | 0–100 percentage for canary |

## CI/CD integration

The `cd.yml` workflow:

1. Builds and pushes API + web images to GHCR on merge to `main`.
2. Deploys to **staging** automatically.
3. Runs smoke tests against `STAGING_API_URL`.
4. **Production** deploy requires manual `workflow_dispatch` with environment approval.
