#!/usr/bin/env bash
# Audit backend lockfile with `uv audit`. Exit 0 always (advisory / non-blocking).
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

UV_BIN=""
if command -v uv >/dev/null 2>&1 && uv audit --help >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
fi

if [[ -z "$UV_BIN" ]]; then
  CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/filmony/uv-audit"
  mkdir -p "$CACHE_DIR"
  if [[ ! -x "$CACHE_DIR/uv" ]] || ! "$CACHE_DIR/uv" audit --help >/dev/null 2>&1; then
    echo 'security-audit-backend: installing a uv build with `audit` into cache…' >&2
    curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR="$CACHE_DIR" sh >/dev/null
  fi
  if [[ -x "$CACHE_DIR/uv" ]] && "$CACHE_DIR/uv" audit --help >/dev/null 2>&1; then
    UV_BIN="$CACHE_DIR/uv"
  fi
fi

if [[ -z "$UV_BIN" ]]; then
  echo 'security-audit-backend: could not obtain uv with `audit`; skip' >&2
  exit 0
fi

set +e
"$UV_BIN" audit --frozen --preview-features audit-command
status=$?
set -e

if [[ "$status" -eq 0 ]]; then
  echo 'security-audit-backend: no known vulnerabilities'
else
  echo "security-audit-backend: audit finished with findings (exit ${status}; non-blocking)" >&2
fi
exit 0
