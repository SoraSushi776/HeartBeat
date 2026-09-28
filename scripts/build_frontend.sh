#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"
if [[ ! -d node_modules ]]; then
  npm install --registry=https://registry.npmmirror.com
fi
npm run build
echo "Frontend built at frontend/dist"
