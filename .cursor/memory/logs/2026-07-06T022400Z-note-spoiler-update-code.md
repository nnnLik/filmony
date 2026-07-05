# Action Log

- **Timestamp:** 2026-07-06T02:24:00Z
- **Feature slug:** note-spoiler-update
- **Action type:** code
- **Summary:** Лимит watch_note 1000, spoiler tokens ⟦S⟧…⟦/S⟧, composer UI и рендер.
- **Files:**
  - `backend/src/const/text_limits.py`
  - `backend/src/services/text/spoiler_tokens.py`
  - `backend/src/migrations/versions/z1a2b3c4d567_user_card_watch_note_len_1000.py`
  - `frontend/src/lib/spoilerTokens.ts`
  - `frontend/src/components/comments/CommentSpoilerToggleButton.tsx`
  - `frontend/src/components/comments/SpoilerRevealBlock.tsx`
  - `frontend/src/components/comments/CommentBodyWithReactionTokens.tsx`
- **Verification:** `cd frontend && npm run lint && npm run build`; vitest `spoilerTokens.test.ts` 4 passed
