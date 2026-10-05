#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export HEARTBEAT_DATA_DIR="${HEARTBEAT_DATA_DIR:-$ROOT/data}"
export HEARTBEAT_PORT="${1:-${HEARTBEAT_PORT:-8000}}"
if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$HEARTBEAT_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port $HEARTBEAT_PORT is already listening, pick another one" >&2
  exit 1
fi
exec .venv/bin/python -m heartbeat.server.main
