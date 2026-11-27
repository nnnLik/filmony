#!/usr/bin/env bash
# Audit frontend lockfile with `npm audit`. Exit 0 always (advisory / non-blocking).
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"

if ! command -v npm >/dev/null 2>&1; then
  echo 'security-audit-frontend: npm not found; skip' >&2
  exit 0
fi

set +e
npm audit --package-lock-only
status=$?
set -e

if [[ "$status" -eq 0 ]]; then
  echo 'security-audit-frontend: no known vulnerabilities'
else
  echo "security-audit-frontend: audit finished with findings (exit ${status}; non-blocking)" >&2
fi
exit 0
