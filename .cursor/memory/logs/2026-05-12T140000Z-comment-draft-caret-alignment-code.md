# Action log

- **Timestamp:** 2026-05-12T140000Z
- **Feature slug:** comment-draft-caret-alignment
- **Action type:** code

## Summary
Восстановлено отображение реакций и @-чипов в зеркале черновика; нативный курсор скрыт, добавлен overlay-курсор по геометрии `Range` и `data-char-*` на сегментах; экспорт `splitCommentTextIntoSegmentsWithRanges`.

## Files
- `frontend/src/components/comments/CommentDraftMirrorField.tsx`
- `frontend/src/components/comments/CommentBodyWithReactionTokens.tsx`
- `frontend/src/lib/commentReactionTokens.ts`
- `frontend/src/lib/commentDraftCaretGeometry.ts`
- `docs/features/comment-draft-caret-alignment.md`
- `.cursor/active/comment-draft-caret-alignment/result.md`

## Verification
- `cd frontend && npm run lint && npm run build` (exit 0)
