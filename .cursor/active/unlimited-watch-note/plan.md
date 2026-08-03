# Plan: unlimited-watch-note (backend)

1. Model: `user_card.watch_note` → `Text`.
2. Migration `f1e2d3c4b567`: alter column String(1000) → Text.
3. Remove `WATCH_NOTE_MAX_LEN` and length checks from card/watchlist services.
4. Remove `max_length=1000` from API schemas (`cards`, `profile`, `watchlist`).
5. Delete `backend/src/const/text_limits.py` (only held watch note limit).
6. Tests: replace reject-over-1000 with accept-over-1000 create + patch.
