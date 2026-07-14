#!/bin/sh
# Deploy standalone landing to Cloudflare Workers (static assets)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

"$ROOT/scripts/build-landing-preview.sh"

if command -v wrangler >/dev/null 2>&1; then
  WRANGLER=wrangler
else
  WRANGLER="npx --yes wrangler@4"
fi

echo "Deploying to Cloudflare Worker: super-tooth-39f3"
$WRANGLER deploy

echo "OK: https://super-tooth-39f3.xassaggii.workers.dev"
