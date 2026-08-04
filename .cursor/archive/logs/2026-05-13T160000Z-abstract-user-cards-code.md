# Action log fragment

**Timestamp:** 2026-05-13T160000Z

**Feature slug:** abstract-user-cards

**Action type:** code

## Summary

Added `CatalogItem`, extended `MovieCard` with nullable `film_id`, nullable `catalog_item_id`, partial unique indexes for `(user_id, catalog_item_id)` and `(user_id, film_id)` when respective columns are present. Alembic revision `u1v2w3x4y890` creates `catalog_item`, backfills from `film` (provider `kinopoisk`), links existing `movie_card` rows via `film_id`, drops global `uq_movie_card_user_film`.

## Files

- `backend/src/models/catalog_item.py`
- `backend/src/models/movie_card.py`
- `backend/src/models/__init__.py`
- `backend/src/migrations/versions/u1v2w3x4y890_universal_user_cards.py`
- `backend/src/tests/models/test_movie_card_catalog_schema.py`
- `.cursor/active/abstract-user-cards/progress.md`
- `.cursor/memory/logs/action-log.md`
- `.cursor/memory/logs/2026-05-13T160000Z-abstract-user-cards-code.md`

## Verification

- `docker compose -f docker-compose.yml exec -w /opt/app backend ruff check …` (`__all__` sort fixed via `ruff check --fix`)
- `docker compose exec -w /opt/app backend pytest src/tests/models/test_movie_card_catalog_schema.py -q` — 4 passed
- `docker compose exec -w /opt/app backend alembic upgrade head` — applied `n0o1p2q3r678 -> u1v2w3x4y890`
- `docker compose exec -w /opt/app backend pytest src/tests/api/test_share_movie_card.py::test_share_movie_card_queues_tasks_for_followers -q` — 1 passed
