# Comment Header Actions Overflow

## Goal
Replace inline comment action text links with a compact header: Reply icon plus an overflow menu for owner actions; hide taste-match % on own comments.

## Behavior
- **Reply:** always shown as an `IconButton` when reply is available.
- **Owner actions:** Edit, Delete, and To-feed move into a ⋯ overflow menu (same permission rules as before).
- **Taste badge:** taste-match percentage is not shown when the comment author is the current user.

## Key Components
- `frontend/src/components/comments/CommentHeaderActions.tsx` — Reply + overflow shell and owner menu items.
- `frontend/src/components/tasteQuiz/TasteQuizCommentAuthorBadge.tsx` — own-comment taste % suppression.
- `frontend/src/pages/MovieCardDetailPage.tsx`, `frontend/src/pages/FeedPostDetailPage.tsx` — detail thread wiring.
- `frontend/src/components/feed/FeedCard.tsx`, `frontend/src/components/feed/FeedPostCard.tsx` — feed comment previews.

## Verification
```bash
cd frontend && npm run lint && npm run build
```
Status: passed (2026-07-27, exit 0).

## Limitations
- No dedicated automated tests for the new overflow layout yet.
