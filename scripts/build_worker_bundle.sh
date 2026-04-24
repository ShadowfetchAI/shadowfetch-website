#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WORKER_OUT="$ROOT_DIR/.cloudflare/worker"

mkdir -p "$WORKER_OUT"

cd "$ROOT_DIR"

npm run build
npx wrangler pages functions build functions \
  --project-directory . \
  --build-output-directory dist \
  --outdir "$WORKER_OUT" \
  --output-config-path "$WORKER_OUT/generated-config.json" \
  --output-routes-path "$WORKER_OUT/_routes.json"

echo "Worker bundle ready at $WORKER_OUT"
