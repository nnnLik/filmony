# Action log fragment

- **Timestamp:** 2026-05-14T16:30:00Z
- **Feature slug:** abstract-user-cards
- **Action type:** code + test

## Summary

Added card-level catalog subject on legacy `movie_card` / `UserCard`: NOT NULL `provider` (`CatalogProvider`: `kinopoisk`, `no_provider`), nullable `external_id`, Alembic backfill from `catalog_item` / `film` / manual rows, partial unique `(user_id, provider, external_id)` for Kinopoisk non-null externals. Extended create/read (detail, feed, profile list, CSV export), `POST /cards` Kinopoisk `provider` + `external_id` path (delegates to catalog-backed create when `catalog_item` exists). `/api/catalog/resolve` rejects `no_provider` without remote search.

## Files

- `backend/src/models/catalog_item.py`
- `backend/src/models/user_card.py`
- `backend/src/migrations/versions/y9z0a1b2c345_movie_card_provider_subject.py`
- `backend/src/services/cards/create_movie_card.py`
- `backend/src/services/cards/get_movie_card_details.py`
- `backend/src/services/cards/list_movie_card_feed.py`
- `backend/src/services/profile/list_user_movie_cards.py`
- `backend/src/services/catalog/resolve_catalog_item_service.py`
- `backend/src/services/profile/export_my_movie_cards_csv_telegram.py`
- `backend/src/api/cards/schemas.py`
- `backend/src/api/cards/routes.py`
- `backend/src/api/feed/routes.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/tests/api/test_cards_routes.py`
- `backend/src/tests/api/test_catalog_routes.py`
- `backend/src/tests/models/test_movie_card_catalog_schema.py`
- `backend/src/tests/api/test_profile_routes.py`
- `backend/src/tests/api/test_following_ratings_for_movie_card.py`
- `backend/src/tests/api/test_feed_posts_routes.py`
- `backend/src/tests/api/test_search_routes.py`
- `backend/src/tests/api/test_movie_card_feed_recommendation.py`
- `backend/src/tests/api/test_film_community_routes.py`
- `backend/src/tests/api/test_me_cards_export_csv.py`

## Verification

- `docker compose exec -w /opt/app backend pytest -q` → **223 passed**
- `docker compose exec backend ruff check src --fix`
- `docker compose exec backend alembic upgrade head` → revision `y9z0a1b2c345`

## Links

- Migration head: `y9z0a1b2c345` (revises `w3x4y5z6a012`)
