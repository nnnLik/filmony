# Unlimited watch_note length

User card descriptions (`watch_note`) are no longer capped at 1000 characters on the backend.

## Backend
- Column `user_card.watch_note` is `Text` (migration `f1e2d3c4b567`).
- API schemas for cards, profile watchlist, and watchlist entries omit `max_length` on `watch_note`.
- Services normalize with strip + spoiler validation only; no length check.
- Removed `backend/src/const/text_limits.py` (`WATCH_NOTE_MAX_LEN`).

## Tests
- `test_create_card_watch_note_accepts_over_1000_chars`
- `test_patch_card_watch_note_accepts_over_1000_chars`

## Unchanged
- Telegram caption truncation at 1000 characters.
- Comment/post/share text limits.
