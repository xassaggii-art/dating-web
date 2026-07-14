#!/bin/sh
# Standalone landing for zip / Netlify Drop / GitHub Pages
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/preview-landing"
rm -rf "$OUT"
mkdir -p "$OUT/static/css" "$OUT/static/js" "$OUT/static/images/landing"
sed 's|/static/|static/|g' "$ROOT/web/landing.html" > "$OUT/index.html"
cp "$ROOT/web/static/css/landing.css" "$OUT/static/css/"
cp "$ROOT/web/static/js/landing.js" "$OUT/static/js/"
cp -R "$ROOT/web/static/images/landing/." "$OUT/static/images/landing/"
(cd "$ROOT" && zip -qr preview-landing.zip preview-landing)
echo "OK: $OUT"
echo "ZIP: $ROOT/preview-landing.zip"
echo "Local: cd preview-landing && python3 -m http.server 8080"
