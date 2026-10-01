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
"$PYTHON" -m pip install -q nuitka ordered-set zstandard

echo "==> locating pyside6-deploy"
DEPLOY="${ROOT}/.venv/bin/pyside6-deploy"
if [[ ! -x "$DEPLOY" ]]; then
  DEPLOY="$(command -v pyside6-deploy || true)"
fi
if [[ -z "$DEPLOY" || ! -x "$DEPLOY" ]]; then
  echo "[FAIL] pyside6-deploy not found." >&2
  echo "       It ships inside PySide6, not on PyPI. Locate it with:" >&2
  echo "         \"$PYTHON\" -c \"import PySide6, pathlib; print(pathlib.Path(PySide6.__file__).parent)\"" >&2
  echo "       then reinstall PySide6 into ${ROOT}/.venv." >&2
  exit 1
fi

# pyside6-deploy decides whether to prompt the user by reading VIRTUAL_ENV only,
# so a venv that was never activated looks like a bare interpreter to it.
if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  export VIRTUAL_ENV="${ROOT}/.venv"
  export PATH="${ROOT}/.venv/bin:${PATH}"
fi

echo "==> preparing deployment spec"
# --force turns pyside6-deploy prompts into a yes; Nuitka has its own prompts that
# only the spec can silence, so prepare_deploy_spec.py injects them into extra_args.
"$PYTHON" scripts/prepare_deploy_spec.py "$DEPLOY" heartbeat/client/main.py

echo "==> running pyside6-deploy ($DEPLOY)"
# pyside6-deploy writes pysidedeploy.spec next to the entry
"$DEPLOY" --force heartbeat/client/main.py

echo "==> done. Look for HeartBeat client artifact under ${ROOT}"
