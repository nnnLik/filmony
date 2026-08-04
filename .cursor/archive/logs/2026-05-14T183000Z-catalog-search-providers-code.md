# Action log fragment

**Timestamp:** 2026-05-14T183000Z  
**Feature slug:** catalog-search-providers  
**Action type:** refactor

## Summary

Backend card-first naming pass: renamed user-card services/modules/DTOs/API schema classes from legacy `MovieCard` / `*_movie_card_*` to `UserCard` / `*_user_card_*` where behavior is unchanged; domain models use card-centric field names (`referenced_inline_user_cards`, `referenced_user_card_id`, `user_card_id`, reaction batch `user_card_ids`, inline snippet `ReferencedInlineUserCardSnippet`, merge-state `tail_linked_film_ids`); profile listing types `UserCardListItem` / `UserCardListPage` / `ListUserCardsService`; Telegram runner symbols aligned while **Celery task registry names** stay `notify_movie_card_*` / `deliver_shared_movie_card` for worker compatibility.

## Files

- Renamed modules under `backend/src/services/cards/` (e.g. `list_user_card_feed.py`, `create_user_card.py`, `inline_user_card_ref_tokens.py`, …), `backend/src/services/profile/` (`list_user_cards.py`, …), `backend/src/services/telegram/` (`notify_user_card_*.py`, `notify_shared_user_card.py`)
- API: `backend/src/api/cards/` (routes, schemas, feed mapping), `backend/src/api/profile/` (schemas, me/users routes), `backend/src/api/feed/routes.py`, `backend/src/api/feed_posts/routes.py`
- Infra: `backend/src/services/reactions/get_reaction_summaries_for_targets.py`, `backend/src/tasks/telegram_engagement.py`
- Tests: `backend/src/tests/api/test_engagement_telegram_notifications.py` (patch path), full suite green

## Verification

- `make backend-fix && make backend-lint` — pass  
- `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest -q` — **267 passed**

## Links

- `.cursor/active/catalog-search-providers/progress.md`
- `.cursor/active/catalog-search-providers/result.md`
