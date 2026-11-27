#!/usr/bin/env bash
# Audit backend lockfile with `uv audit`. Exit 0 always (advisory / non-blocking).
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

if ! command -v uv >/dev/null 2>&1; then
  echo 'security-audit-backend: uv not found; skip' >&2
  exit 0
fi

if ! uv audit --help >/dev/null 2>&1; then
  echo 'security-audit-backend: this uv build has no `audit` (need uv >= 0.13); skip' >&2
  exit 0
fi

set +e
uv audit --frozen --preview-features audit-command
status=$?
set -e

if [[ "$status" -eq 0 ]]; then
  echo 'security-audit-backend: no known vulnerabilities'
else
  echo "security-audit-backend: audit finished with findings (exit ${status}; non-blocking)" >&2
fi
exit 0
