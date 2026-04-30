#!/usr/bin/env sh
set -eu

alembic upgrade head

set -- uvicorn src.main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8000}"
if [ "${APP_RELOAD:-false}" = "true" ]; then
  set -- "$@" --reload
fi

exec "$@"
