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

echo ""
echo "== Toolchain =="
for cmd in python ruby; do
  if command -v "$cmd" >/dev/null 2>&1; then
    version=$("$cmd" --version 2>&1 | head -1)
    echo "OK: $cmd ($version)"
  else
    echo "MISSING: $cmd (run: mise install)"
    errors=$((errors + 1))
  fi
done

echo ""
if [[ "$errors" -gt 0 ]]; then
  echo "Doctor found $errors issue(s)."
  exit 1
fi

echo "All checks passed."
