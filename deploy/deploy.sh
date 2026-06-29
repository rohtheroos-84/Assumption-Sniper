#!/usr/bin/env bash
# Deploy to staging or production with optional canary traffic shift.
set -euo pipefail

ENV="${1:-staging}"
CANARY_PERCENT="${2:-0}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ "$ENV" != "staging" && "$ENV" != "production" ]]; then
  echo "usage: deploy.sh [staging|production] [canary_percent]"
  exit 1
fi

echo "==> building images for $ENV"
docker compose -f "$ROOT/docker-compose.yml" build api web

if [[ "$ENV" == "staging" ]]; then
  echo "==> deploying staging"
  docker compose -f "$ROOT/docker-compose.yml" -f "$ROOT/docker-compose.staging.yml" up -d api web
  echo "==> running smoke tests"
  python "$ROOT/apps/api/scripts/smoke_test.py" --url "${STAGING_API_URL:-http://localhost:8000}"
  echo "staging deploy complete"
  exit 0
fi

# Production: blue/green with optional canary
ACTIVE_SLOT="${TRAFFIC_SLOT:-blue}"
TARGET_SLOT="green"
if [[ "$ACTIVE_SLOT" == "green" ]]; then
  TARGET_SLOT="blue"
fi

echo "==> deploying production slot: $TARGET_SLOT (canary ${CANARY_PERCENT}%)"
export DEPLOY_SLOT="$TARGET_SLOT"
docker compose -f "$ROOT/docker-compose.production.yml" --profile "$TARGET_SLOT" up -d

python "$ROOT/apps/api/scripts/smoke_test.py" --url "${PRODUCTION_API_URL:-http://localhost:8000}"

if [[ "$CANARY_PERCENT" -gt 0 ]]; then
  echo "==> canary: routing ${CANARY_PERCENT}% traffic to $TARGET_SLOT"
  export CANARY_SLOT="$TARGET_SLOT"
  export CANARY_PERCENT="$CANARY_PERCENT"
else
  echo "==> promoting $TARGET_SLOT to 100% traffic"
  export TRAFFIC_SLOT="$TARGET_SLOT"
fi

echo "production deploy complete (active slot: ${TRAFFIC_SLOT:-$TARGET_SLOT})"
