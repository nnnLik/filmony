# Unlimited watch_note length

## Scope
- Remove the 1000-character limit on user card `watch_note` (card description/note) on the backend.
- DB column `user_card.watch_note` becomes unbounded `Text`.
- API schemas and service validation must not reject notes solely for length > 1000.
- Spoiler token validation remains unchanged.

## Acceptance criteria
- `POST /api/cards` and `PATCH /api/cards/:id` accept `watch_note` longer than 1000 characters.
- Watchlist create/update paths that set `watch_note` accept long notes.
- Alembic migration alters column from `String(1000)` to `Text` without editing prior migrations.
- Tests assert acceptance of notes > 1000 on create and patch.
- Telegram caption truncation helpers at 1000 chars remain unchanged.

## Out of scope
- Frontend limit removal (separate slice).
- Other text limits (comments, posts, share_comment).
