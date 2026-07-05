# Result: note-spoiler-update

Status: **completed**

## Implemented
- Лимит заметок карточки **1000** символов (`backend/src/const/text_limits.py`, migration `z1a2b3c4d567`, schemas/services, `frontend/src/lib/watchNoteLimits.ts`).
- Спойлеры как токены **`⟦S⟧…⟦/S⟧`**: валидация `backend/src/services/text/spoiler_tokens.py`, интеграция в comments/posts/watch notes.
- UI: `CommentSpoilerToggleButton`, `SpoilerRevealBlock`, рендер в `CommentBodyWithReactionTokens`.
- Composer-кнопка во всех целевых экранах.

## Changed files (main)
- Backend: `const/text_limits.py`, `services/text/spoiler_tokens.py`, `services/cards/create_user_card.py`, `update_user_card.py`, `comment_reaction_tokens.py`, `feed_posts/validate_feed_post_body.py`, watchlist services, `api/*/schemas.py`, `models/user_card.py`, migration.
- Frontend: `lib/spoilerTokens.ts`, `lib/watchNoteLimits.ts`, `CommentBodyWithReactionTokens.tsx`, composer pages/components.
- Tests: `backend/src/tests/services/test_spoiler_tokens.py`, `test_cards_routes.py`, `frontend/src/lib/__tests__/spoilerTokens.test.ts`.

## Verification
- `cd frontend && npm run lint && npm run build` — OK
- `npm run test -- src/lib/__tests__/spoilerTokens.test.ts` — 4 passed
- Backend: `make backend-test-one target=src/tests/services/test_spoiler_tokens.py` (requires Docker backend with deps; added tests ready)

## Limitations
- Без вложенных спойлеров.
- `share_comment` остаётся 500 символов.
