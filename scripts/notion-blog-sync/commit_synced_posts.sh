#!/usr/bin/env bash
# Stage Notion-synced posts/assets, then commit (and optionally push) if the
# index changed.
#
# git add MUST run before the "anything to commit?" check. Untracked files do
# not appear in `git diff` or `git diff --cached`, so checking first made the
# Action exit 0 with "No changes to commit" while dropping brand-new
# Published posts (Topic #2).
set -euo pipefail

PUSH=0
if [[ "${1:-}" == "--push" ]]; then
  PUSH=1
fi

mkdir -p _posts blog/assets
git add -- _posts blog/assets

untracked="$(git ls-files --others --exclude-standard -- _posts blog/assets || true)"
if [[ -n "${untracked}" ]]; then
  echo "::error::Untracked files remain under _posts or blog/assets after git add:"
  printf '%s\n' "${untracked}"
  exit 1
fi

if git diff --cached --quiet -- _posts blog/assets; then
  echo "No changes to commit."
  exit 0
fi

git commit -m "chore(blog): sync Published posts from Notion"

if [[ "${PUSH}" -eq 1 ]]; then
  git push origin HEAD
fi
