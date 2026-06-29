#!/usr/bin/env bash
# Roll back to the previous deployment slot or image tag.
set -euo pipefail

ENV="${1:-staging}"
PREVIOUS_TAG="${2:-previous}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "==> rolling back $ENV to tag $PREVIOUS_TAG"

if [[ "$ENV" == "production" ]]; then
  CURRENT="${TRAFFIC_SLOT:-blue}"
  ROLLBACK_SLOT="green"
  if [[ "$CURRENT" == "green" ]]; then
    ROLLBACK_SLOT="blue"
  fi
  export TRAFFIC_SLOT="$ROLLBACK_SLOT"
  export API_IMAGE="${API_IMAGE%:*}:$PREVIOUS_TAG"
  export WEB_IMAGE="${WEB_IMAGE%:*}:$PREVIOUS_TAG"
  docker compose -f "$ROOT/docker-compose.production.yml" --profile "$ROLLBACK_SLOT" up -d
  python "$ROOT/apps/api/scripts/smoke_test.py" --url "${PRODUCTION_API_URL:-http://localhost:8000}"
  echo "rollback complete: traffic on slot $ROLLBACK_SLOT"
  exit 0
fi

export API_IMAGE="${API_IMAGE%:*}:$PREVIOUS_TAG"
export WEB_IMAGE="${WEB_IMAGE%:*}:$PREVIOUS_TAG"
docker compose -f "$ROOT/docker-compose.yml" -f "$ROOT/docker-compose.staging.yml" up -d api web
python "$ROOT/apps/api/scripts/smoke_test.py" --url "${STAGING_API_URL:-http://localhost:8000}"
echo "staging rollback complete"
