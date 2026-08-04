# 2026-08-04T170000Z — feed-post-delete-menu closeout

- **Feature:** `feed-post-delete-menu`
- **Action:** Author-only post delete API + overflow menu (Изменить / Удалить) on own feed posts
- **Verification:** `make backend-test-one` (3 delete tests passed); `npm run lint && npm run build` (exit 0)

## Files

- `backend/src/services/feed_posts/delete_feed_post.py`
- `backend/src/api/feed_posts/routes.py`
- `backend/src/tests/api/test_feed_posts_routes.py`
- `frontend/src/api/feedPostApi.ts`
- `frontend/src/components/feed/PostHeaderActions.tsx`
- `frontend/src/components/feed/FeedPostCard.tsx`
- `frontend/src/pages/FeedPage.tsx`
- `frontend/src/pages/FeedPostDetailPage.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `docs/features/feed-post-delete-menu.md`
