# Comment Header Actions Overflow — Plan

Status: in_progress

## Approach
1. Add `CommentHeaderActions` with Reply icon and owner overflow menu.
2. Refactor `CommentOwnerActionLinks` to feed the overflow menu.
3. Wire detail pages and feed comment cards to the new header actions.
4. Hide taste % in `TasteQuizCommentAuthorBadge` for own comments.
5. Run `npm run lint` and `npm run build`; publish delivery docs.

## Notes
- Reuse `@telegram-apps/telegram-ui` `IconButton` and existing owner-action callbacks.
- Verification pending sibling agent (lint/build).
