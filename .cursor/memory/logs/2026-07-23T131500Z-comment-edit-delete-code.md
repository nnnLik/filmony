# Action log entry

- **Timestamp:** 2026-07-23T131500Z
- **Feature slug:** comment-edit-delete
- **Action type:** code
- **Summary:** Implemented author-only edit/delete for feed post and user card comments (backend services, routes, frontend UI, pytest).
- **Files:**
  - `backend/src/services/feed_posts/update_feed_post_comment.py`
  - `backend/src/services/feed_posts/delete_feed_post_comment.py`
  - `backend/src/services/cards/update_user_card_comment.py`
  - `backend/src/services/cards/delete_user_card_comment.py`
  - `backend/src/api/feed_posts/routes.py`
  - `backend/src/api/cards/routes.py`
  - `backend/src/tests/api/test_feed_posts_routes.py`
  - `backend/src/tests/api/test_cards_routes.py`
  - `frontend/src/pages/FeedPostDetailPage.tsx`
  - `frontend/src/pages/MovieCardDetailPage.tsx`
  - `frontend/src/components/comments/CommentOwnerActionLinks.tsx`
  - `docs/features/comment-edit-delete.md`
- **Verification:** `make backend-test-one` (4 new tests passed); `cd frontend && npm run lint && npm run build`
