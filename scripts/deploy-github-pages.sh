#!/bin/sh
# Publish preview-landing to gh-pages branch (for GitHub Pages)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

"$ROOT/scripts/build-landing-preview.sh"

WORKTREE="$ROOT/.gh-pages-worktree"
rm -rf "$WORKTREE"
git worktree add --orphan gh-pages "$WORKTREE" 2>/dev/null || true

if [ ! -d "$WORKTREE/.git" ]; then
  rm -rf "$WORKTREE"
  git worktree add -B gh-pages "$WORKTREE"
fi

cd "$WORKTREE"
git rm -rf . 2>/dev/null || true
cp -R "$ROOT/preview-landing/." .
touch .nojekyll
git add -A
git commit -m "Deploy landing $(date -u +%Y-%m-%dT%H:%M:%SZ)" || true
git push -f origin gh-pages

cd "$ROOT"
git worktree remove "$WORKTREE" --force 2>/dev/null || rm -rf "$WORKTREE"

echo "OK: pushed gh-pages branch"
echo "Enable: https://github.com/xassaggii-art/dating-web/settings/pages"
echo "Source: Deploy from branch -> gh-pages -> / (root)"
echo "URL: https://xassaggii-art.github.io/dating-web/"
