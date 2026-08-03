# Action Log

- **Timestamp:** 2026-08-04T09:54:00Z
- **Feature slug:** unlimited-watch-note
- **Action type:** code
- **Summary:** Removed 1000-char cap on user_card.watch_note; Text column migration; updated schemas/services/tests.
- **Files:**
  - `backend/src/models/user_card.py`
  - `backend/src/migrations/versions/f1e2d3c4b567_user_card_watch_note_text.py`
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
- **Verification:** pending `make backend-test` in Docker
