# Watchlist Cards Result

Status: complete

## Summary
- Unified «Позже» watchlist for all providers with optional company, shelf, watch note, and multi-friend invites.
- Dedicated create wizard branch collects details only when user chooses «Позже»; rated flow unchanged on steps 3–4.
- Planned `UserCard` stores watchlist metadata; upgrading to rated card preserves card id and pre-fills note/company/shelf.
- Multi-invite: each mutual friend gets own watchlist entry + Telegram push; actor entry stores full `watch_with_user_ids`.

## Changed Files (wizard details phase)
### Backend
- `backend/src/migrations/versions/w1x2y3z4a05_watchlist_watch_with_user_ids.py`
- `backend/src/models/watchlist_entry.py`
- `backend/src/api/profile/schemas.py`, `backend/src/api/profile/me_routes.py`
- `backend/src/api/watchlist/schemas.py`, `backend/src/api/watchlist/routes.py`
- `backend/src/services/watchlist/create_watchlist_entry.py`
- `backend/src/services/watchlist/create_watchlist_entry_from_film.py`
- `backend/src/services/watchlist/create_watchlist_entry_from_catalog.py`
- `backend/src/services/watchlist/normalize_watch_with_partners.py`
- `backend/src/services/watchlist/list_user_watchlist_entries.py`
- `backend/src/services/cards/create_planned_user_card.py`
- `backend/src/services/cards/get_planned_user_card.py`
- `backend/src/services/cards/create_user_card.py`
- `backend/src/tests/api/test_watchlist_routes.py`
- `backend/src/tests/services/test_create_watchlist_entry_service.py`

### Frontend
- `frontend/src/pages/CreateCardPage.tsx`
- `frontend/src/pages/FilmDetailPage.tsx`
- `frontend/src/components/watchlist/MutualWatchFriendsMultiPicker.tsx`
- `frontend/src/components/profile/WatchlistPosterGrid.tsx`
- `frontend/src/api/profileApi.ts`, `frontend/src/api/profileTypes.ts`
- `frontend/src/api/profileApi.test.ts`

## Verification
- `docker compose exec backend alembic upgrade head` — applied `w1x2y3z4a05`
- `docker exec -w /opt/app filmony-backend pytest -o addopts= src/tests/api/test_watchlist_routes.py src/tests/services/test_create_watchlist_entry_service.py` — 21 passed
- `cd frontend && npm test -- src/api/profileApi.test.ts` — 5 passed
- `cd frontend && npm run lint && npm run build` — passed

## Known limitations
- Re-adding the same title to «Позже» still returns 409 (no PATCH for planned metadata).
- `WatchTag` enum still only `watch_later`.
