# Result: unlimited-watch-note (backend)

**Status:** in_progress — code complete; pytest not run in this session.

## Implemented
- Unbounded `watch_note` in DB (`Text`), API schemas, and services.
- Spoiler validation preserved; no length cap on normalize paths.

## Changed files
- `backend/src/models/user_card.py`
- `backend/src/migrations/versions/f1e2d3c4b567_user_card_watch_note_text.py` (new)
- `backend/src/api/cards/schemas.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/api/watchlist/schemas.py`
- `backend/src/services/cards/create_user_card.py`
- `backend/src/services/cards/update_user_card.py`
- `backend/src/services/cards/create_planned_user_card.py`
- `backend/src/services/watchlist/create_watchlist_entry.py`
- `backend/src/services/watchlist/update_watchlist_entry.py`
- `backend/src/tests/api/test_cards_routes.py`
- `backend/src/const/text_limits.py` (deleted)

## Verification (expected)
- `make backend-test-one target=src/tests/api/test_cards_routes.py::test_create_card_watch_note_accepts_over_1000_chars`
- `make backend-test-one target=src/tests/api/test_cards_routes.py::test_patch_card_watch_note_accepts_over_1000_chars`
- Apply migration: `make migrate` (or project equivalent)

## Remaining references
- Historical migration `z1a2b3c4d567_user_card_watch_note_len_1000.py` (unchanged, as required).
- Frontend `frontend/src/lib/watchNoteLimits.ts` still references removed constant (frontend slice).
