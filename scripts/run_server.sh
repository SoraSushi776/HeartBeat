#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export HEARTBEAT_DATA_DIR="${HEARTBEAT_DATA_DIR:-$ROOT/data}"
exec .venv/bin/python -m heartbeat.server.main
