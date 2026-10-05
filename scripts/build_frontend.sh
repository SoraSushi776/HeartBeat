#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"
if ! npm ls --depth=0 --silent >/dev/null 2>&1; then
  npm install --registry=https://registry.npmmirror.com
fi
npm run build
echo "Frontend built at frontend/dist"
