#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

errors=0

check_path() {
  if [[ ! -e "$1" ]]; then
    echo "MISSING: $1"
    errors=$((errors + 1))
  else
    echo "OK: $1"
  fi
}

echo "== Site files =="
check_path "index.html"
check_path "CNAME"
check_path "css/styles.css"
check_path "js/site.js"
check_path "privacy/index.html"
check_path "tos/index.html"
check_path "assets"
check_path "_config.yml"
check_path "Gemfile"
check_path "blog/index.html"
check_path "_posts"

echo ""
echo "== Toolchain =="
for cmd in python ruby bundle; do
  if command -v "$cmd" >/dev/null 2>&1; then
    version=$("$cmd" --version 2>&1 | head -1)
    echo "OK: $cmd ($version)"
  else
    echo "MISSING: $cmd (run: mise install && bundle install)"
    errors=$((errors + 1))
  fi
done

if command -v bundle >/dev/null 2>&1 && [[ -f Gemfile ]]; then
  if bundle check >/dev/null 2>&1; then
    echo "OK: bundle dependencies"
  else
    echo "MISSING: bundle dependencies (run: bundle install)"
    errors=$((errors + 1))
  fi
fi

echo ""
if [[ "$errors" -gt 0 ]]; then
  echo "Doctor found $errors issue(s)."
  exit 1
fi

echo "All checks passed."
