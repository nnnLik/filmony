# Watchlist Cards Result

Status: complete

## Summary
- Unified watchlist for Kinopoisk, RAWG, and custom cards with provider-aware create/list/delete/presence APIs.
- Watch-with invites: mutual subscription validation, independent entries for both users, Telegram push notification.
- Feed post created on every watchlist add with title, description, and poster (no personal rating).
- Legacy `user_watchlist_film` data migrated and table dropped; film_id shims retained for compatibility.
- Frontend: mutual-friend picker, watch tag selector, profile «Позже» grid with delete and provider-aware navigation, invite deeplinks.

## Changed Files (completion phase)
### Backend
- `backend/src/services/watchlist/assert_mutual_watch_partner.py`
- `backend/src/services/watchlist/create_watchlist_entry.py`
- `backend/src/services/watchlist/create_watchlist_entry_from_film.py`
- `backend/src/services/watchlist/create_watchlist_entry_from_catalog.py`
- `backend/src/services/feed_posts/create_watchlist_feed_post.py`
- `backend/src/services/feed_posts/watchlist_provider_snapshot.py`
- `backend/src/api/profile/me_routes.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/migrations/versions/w1x2y3z4a03_drop_user_watchlist_film.py`
- `backend/src/tests/services/test_create_watchlist_entry_service.py`
- `backend/src/tests/api/test_watchlist_routes.py`
- `backend/src/tests/services/test_create_watchlist_feed_post_service.py`
- `backend/src/tests/migrations/test_watchlist_migration.py`

### Frontend
- `frontend/src/pages/CreateCardPage.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/pages/FilmDetailPage.tsx`
- `frontend/src/components/profile/WatchlistPosterGrid.tsx`
- `frontend/src/components/watchlist/MutualWatchFriendPicker.tsx`
- `frontend/src/lib/mutualSubscriptionFilter.ts`
- `frontend/src/api/profileApi.ts`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/navigation/TelegramMiniAppStartParamRedirect.tsx`
- `frontend/src/lib/miniAppCardDeepLink.ts`
- `frontend/src/api/profileApi.test.ts`

## Verification
- `docker exec -w /opt/app filmony-backend pytest -o addopts= src/tests/api/test_watchlist_routes.py src/tests/services/test_create_watchlist_entry_service.py src/tests/services/test_create_watchlist_feed_post_service.py src/tests/migrations/test_watchlist_migration.py` — 22 passed
- `cd frontend && npm test -- src/api/profileApi.test.ts` — 4 passed
- `cd frontend && npm run lint && npm run build` — passed

## Known limitations
- `WatchTag` enum currently exposes only `watch_later`; UI is ready for future tags.
- Legacy film-specific delete/presence routes kept for FilmDetailPage compatibility.
- Feed posts use `body` + `image_url` rather than `referenced_card_id` (no rated card yet).
