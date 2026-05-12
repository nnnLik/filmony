# Action log

- **Timestamp:** 2026-05-12T120000Z
- **Feature slug:** comment-draft-caret-alignment
- **Action type:** code

## Summary
Исправлено визуальное расхождение курсора с текстом в зеркальных черновиках: зеркало переведено на plain text вместо `CommentBodyWithReactionTokens`; выровнена типографика multiline textarea с зеркалом.

## Files
- `frontend/src/components/comments/CommentDraftMirrorField.tsx`

## Verification
- `cd frontend && npm run lint && npm run build` (exit 0)
