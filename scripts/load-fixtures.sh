#!/usr/bin/env bash
# Load SQL fixtures into filmony-postgres (see compose.yml).
# Usage:
#   ./scripts/load-fixtures.sh              # all fixtures in dependency order
#   ./scripts/load-fixtures.sh user.sql     # one file from fixtures/
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT/compose.yml}"
DC=(docker compose -f "$COMPOSE_FILE")
CONTAINER="${POSTGRES_CONTAINER:-filmony-postgres}"
DB_USER="${POSTGRES_USER:-filmony}"
DB_NAME="${POSTGRES_DB:-filmony}"

load_file() {
  local rel="$1"
  local path="$ROOT/fixtures/$rel"
  if [[ ! -f "$path" ]]; then
    echo "load-fixtures: skip (missing): $rel" >&2
    return 0
  fi
  if [[ ! -s "$path" ]]; then
    echo "load-fixtures: skip (empty): $rel" >&2
    return 0
  fi
  echo "load-fixtures: loading $rel" >&2
  "${DC[@]}" exec -T "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 <"$path"
}

if [[ "${1:-}" ]]; then
  load_file "$1"
  exit 0
fi

# Order respects FKs: user & film -> movie_card -> comments/tags -> subscriptions
ORDER=(
  user.sql
  film.sql
  movie_card.sql
  movie_card_comment.sql
  movie_card_tag.sql
  user_subscription.sql
)

for f in "${ORDER[@]}"; do
  load_file "$f"
done

echo "load-fixtures: done" >&2
