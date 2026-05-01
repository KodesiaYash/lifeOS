#!/usr/bin/env bash
# Deploy AI Life OS onto the host that runs this script.
# Designed for a self-hosted GitHub Actions runner, but safe to run manually.

set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/Desktop/DeploymentHost/lifeOS}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"
APP_SERVICE="${APP_SERVICE:-app}"
AUX_SERVICES=(${AUX_SERVICES:-worker})
INFRA_SERVICES=(${INFRA_SERVICES:-postgres redis minio})
SETUP_SERVICES=(${SETUP_SERVICES:-minio-setup})
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
HEALTH_TIMEOUT_SECONDS="${HEALTH_TIMEOUT_SECONDS:-90}"
ENV_FILE="${ENV_FILE:-.env}"

log() { printf '[deploy %s] %s\n' "$(date +%H:%M:%S)" "$*"; }
fail() { printf '[deploy ERROR] %s\n' "$*" >&2; exit 1; }

command -v docker >/dev/null || fail "docker is not installed or not in PATH"
docker compose version >/dev/null || fail "docker compose plugin is not available"

[ -d "$APP_DIR/.git" ] || fail "$APP_DIR is not a git checkout. Clone the repo there first."
[ -f "$APP_DIR/$ENV_FILE" ] || fail "$APP_DIR/$ENV_FILE is missing. Create it before deploying."
[ -f "$APP_DIR/docker-compose.yml" ] || fail "$APP_DIR/docker-compose.yml is missing."

cd "$APP_DIR"

log "Fetching latest origin/$DEPLOY_BRANCH"
git fetch --prune --tags origin
git checkout "$DEPLOY_BRANCH"
BEFORE_SHA="$(git rev-parse HEAD)"
git reset --hard "origin/$DEPLOY_BRANCH"
AFTER_SHA="$(git rev-parse HEAD)"

if [ "$BEFORE_SHA" = "$AFTER_SHA" ]; then
  log "Already at $AFTER_SHA - rebuilding anyway"
else
  log "Updated $BEFORE_SHA -> $AFTER_SHA"
fi

if [ "${DEPLOY_RELOADED:-0}" != "1" ] && [ "$BEFORE_SHA" != "$AFTER_SHA" ]; then
  log "Re-executing deploy.sh with updated version ($AFTER_SHA)"
  export DEPLOY_RELOADED=1
  exec bash "$APP_DIR/deploy.sh" "$@"
fi

log "Starting infra services: ${INFRA_SERVICES[*]}"
docker compose up -d "${INFRA_SERVICES[@]}"

for service in "${SETUP_SERVICES[@]}"; do
  log "Running setup service: $service"
  docker compose up "$service" --exit-code-from "$service"
done

log "Building services: $APP_SERVICE ${AUX_SERVICES[*]}"
docker compose build "$APP_SERVICE" "${AUX_SERVICES[@]}"

log "Restarting application services"
docker compose up -d "$APP_SERVICE" "${AUX_SERVICES[@]}"

log "Pruning dangling images"
docker image prune -f >/dev/null || true

log "Waiting up to ${HEALTH_TIMEOUT_SECONDS}s for $HEALTH_URL"
deadline=$(( $(date +%s) + HEALTH_TIMEOUT_SECONDS ))
while [ "$(date +%s)" -lt "$deadline" ]; do
  if curl -fsS --max-time 3 "$HEALTH_URL" >/dev/null 2>&1; then
    log "Healthy - commit=$AFTER_SHA"
    exit 0
  fi
  sleep 2
done

log "Health check failed - dumping recent app logs"
docker compose logs --tail 120 "$APP_SERVICE" || true
exit 1
