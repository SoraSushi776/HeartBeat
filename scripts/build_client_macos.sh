#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${ROOT}/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="python3"
fi

"$PYTHON" scripts/generate_icons.py

echo "==> building frontend"
if [[ -x "${ROOT}/frontend/node_modules/.bin/vite" ]] || [[ -d "${ROOT}/frontend/node_modules" ]]; then
  (cd frontend && npm run build)
else
  (cd frontend && npm install --registry=https://registry.npmmirror.com && npm run build)
fi

echo "==> installing packaging tools"
"$PYTHON" -m pip install -q pyside6-deploy nuitka ordered-set zstandard

echo "==> running pyside6-deploy"
# pyside6-deploy writes pysidedeploy.spec next to the entry
"$PYTHON" -m pip show pyside6-deploy >/dev/null
if command -v pyside6-deploy >/dev/null 2>&1; then
  DEPLOY=pyside6-deploy
else
  DEPLOY="$PYTHON -m pyside6_deploy"
fi

$DEPLOY heartbeat/client/main.py || $DEPLOY --help

echo "==> done. Look for HeartBeat client artifact under ${ROOT}"
