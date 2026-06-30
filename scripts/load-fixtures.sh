#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER="${POSTGRES_CONTAINER:-homelab-postgres}"
DB_USER="${POSTGRES_USER:-filmony}"
DB_NAME="${POSTGRES_DB:-filmony}"

if ! docker inspect -f '{{.Id}}' "$CONTAINER" &>/dev/null; then
	echo "load-fixtures: нет контейнера $CONTAINER (homelab-infra make dev-up?)" >&2
	exit 1
fi

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
	docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 <"$path"
}

if [[ "${1:-}" ]]; then
	load_file "$1"
	exit 0
fi

ORDER=(
	user.sql
	user_card_category.sql
	reaction_type.sql
	film.sql
	catalog_game_rawg.sql
	user_card.sql
	user_card_favorite_updates.sql
	user_watchlist_film.sql
	card_comment.sql
	user_reaction.sql
	card_tag.sql
	user_subscription.sql
	feed_post.sql
)

for f in "${ORDER[@]}"; do
	load_file "$f"
done

echo "load-fixtures: done" >&2
