# 2026-08-24T160300Z-colon-shortcode-markup-code

- Timestamp: 2026-08-24T160300Z
- Feature slug: `colon-shortcode-markup`
- Action type: `code`
- Summary: Discord-like `:shortcode:` autocomplete in comment compose (shared parser, hook, portal) and expand legacy `⟦r{id}⟧` / `[[r{id}]]` to `:shortcode:` when entering comment edit.

## Files
- `frontend/src/lib/commentShortcodeCompose.ts`
- `frontend/src/lib/__tests__/commentShortcodeCompose.test.ts`
- `frontend/src/lib/commentReactionTokens.ts`
- `frontend/src/lib/__tests__/commentReactionTokens.test.ts`
- `frontend/src/hooks/useReactionShortcodePicker.ts`
- `frontend/src/hooks/useCommentDraftEditor.ts`
- `frontend/src/components/comments/ReactionShortcodeSuggestPortal.tsx`
- `frontend/src/components/comments/CommentComposeBar.tsx`
- `frontend/src/components/comments/CommentThreadSection.tsx`
- `frontend/src/components/comments/CommentListItem.tsx`
- `frontend/src/pages/MovieCardDetailPage.tsx`
- `frontend/src/pages/FeedPostDetailPage.tsx`

## Verification
- `cd frontend && npm test`: 156 passed (parse `:ga` / `10:30` / closing `:gasp:`; expand `⟦r12⟧` → `:gasp:`)
- `cd frontend && npm run lint`: no new issues
- `cd frontend && npx tsc -b`: passed
- `vite build` not run to completion here (Cloudflare plugin `registerHooks` on this Node image)
