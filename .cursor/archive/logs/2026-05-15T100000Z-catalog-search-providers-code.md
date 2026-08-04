# Action log fragment

**Timestamp:** 2026-05-15T100000Z  
**Feature slug:** catalog-search-providers  
**Action type:** code

## Summary

Expose universal `release_year` / `release_date` on card APIs from `Film.year` or `Game.released`; fix joins via `CatalogItem` + `coalesce` (no correlating scalar subquery); align feed/profile/detail UI and RAWG create flow (stop stuffing subtitle into `display_summary`).

## Files

- `backend/src/services/cards/card_catalog_release_fields.py`
- `backend/src/services/cards/get_movie_card_details.py`
- `backend/src/services/cards/list_movie_card_feed.py`
- `backend/src/services/profile/list_user_movie_cards.py`
- `backend/src/services/profile/list_user_feed_posts.py`
- `backend/src/services/feed_posts/get_feed_post_feed_item.py`
- `backend/src/api/cards/schemas.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/api/cards/routes.py`
- `backend/src/api/cards/feed_post_feed_mapping.py`
- `backend/src/api/feed/routes.py`
- `backend/src/tests/services/cards/test_card_catalog_release_fields.py`
- `backend/src/tests/api/test_cards_routes.py`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/api/feedInFeedTypes.ts`
- `frontend/src/lib/movieCardDisplay.ts`
- `frontend/src/pages/MovieCardDetailPage.tsx`
- `frontend/src/components/feed/FeedCard.tsx`
- `frontend/src/components/feed/FeedPostCard.tsx`
- `frontend/src/pages/CreateCardPage.tsx`

## Verification

- `make backend-test-one target='src/tests/api/test_cards_routes.py::test_get_rawg_game_card_detail_has_release_fields'` — pass
- `docker compose … exec … pytest src/tests/services/cards/test_card_catalog_release_fields.py` — pass
- `docker compose … exec … ruff check` (touched backend paths) — pass
- `cd frontend && npm run lint && npm run build` — pass
