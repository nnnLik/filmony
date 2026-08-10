# Actor cast profile stats

## Summary

Full Kinopoisk `ACTOR` cast for **rated** films only (see [film-cast-store-all](./film-cast-store-all.md) — no longer capped at 10). Cast is synced on rated card create/upgrade and via backfill. Profile stats show actor distribution; users can open a user-scoped actor detail page and filter rated cards by actor.

## Backend

### Data model

- **`person`** — Kinopoisk person id, name, photo URL
- **`film_actor`** — film ↔ person with billing order and trimmed role text

### Cast sync

- **`EnsureFilmCastService`** — fetches Kinopoisk staff, parses all `ACTOR` rows, upserts persons, inserts `film_actor`. Idempotent (skips if rows exist; `force=True` replaces cast). KP errors logged, not propagated.
- Hooked in **`CreateUserCardService`** after meaningful rated create and planned→rated upgrade.
- **`manage_backfill_film_cast.py`** — backfill historical rated films (`--dry-run`, `--limit`, `--sleep`, `--batch-size`).

### Profile & API

- **`GetUserCardStatsService`**: `actor_distribution` (top 20), `top_actor_kinopoisk_id`, `top_actor_name` (rated cards only). See [profile-actors-top20](./profile-actors-top20.md) — donut and `unique_actors_count` removed.
- **`list_user_cards`**: query `actor_kinopoisk_id` (AND with director filter).
- **`GET /api/actors/{kinopoisk_id}`** — actor summary for a user (`user_id` query, default viewer).
- **`GET /api/actors/{kinopoisk_id}/films`** — rated films featuring the actor for that user.

## Frontend

- **Profile stats** — «Любимый актёр» insight, «По актёрам» collapsible list (top 20, 10 visible by default); links to `/actors/:id?userId=`. Replaces donut — [profile-actors-top20](./profile-actors-top20.md).
- **`ActorDetailPage`** — summary + rated films list with role
- **Rated cards filter** — actor chip from `actor_distribution` (no extra endpoint)

## Key files

- `backend/src/services/cast/ensure_film_cast.py`
- `backend/src/manage_backfill_film_cast.py`
- `backend/src/services/profile/get_user_card_stats.py`
- `backend/src/api/actors/routes.py`
- `frontend/src/pages/ActorDetailPage.tsx`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`

## Design spec

`docs/superpowers/specs/2026-08-08-actor-cast-profile-stats-design.md`

## Verification

```bash
make backend-test-unit
make backend-test-one target=src/tests/integration/api/test_actors_routes.py
cd frontend && npm run lint && npm run build
```

## Operations

```bash
# After deploy
alembic upgrade head
python -m manage_backfill_film_cast --dry-run
python -m manage_backfill_film_cast --sleep 0.5
```
