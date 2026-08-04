# Result — feed-post-delete-menu

**Status:** completed  
**Closed:** 2026-08-04

## Implemented

- **Backend:** `DeleteFeedPostService` — author-only hard delete; comments removed via DB `ON DELETE CASCADE`.
- **API:** `DELETE /api/feed-posts/{post_id}` → `204`; `404` not found, `403` non-owner.
- **Frontend:** `PostHeaderActions` overflow menu (⋯ → **Изменить** / **Удалить**) on own posts in `FeedPostCard`; inline «Редактировать» text button removed.
- **Delete flow:** `window.confirm` before API; parents remove card / navigate away via `onPostDeleted`.
- **Surfaces:** feed (`FeedPage`), post detail (`FeedPostDetailPage`), profile lists (`ProfilePage`, `PublicProfilePage`).

## Changed files

| Area | File |
|------|------|
| Backend | `backend/src/services/feed_posts/delete_feed_post.py` |
| Backend | `backend/src/services/feed_posts/__init__.py` |
| Backend | `backend/src/api/feed_posts/routes.py` |
| Backend | `backend/src/tests/api/test_feed_posts_routes.py` |
| Frontend | `frontend/src/api/feedPostApi.ts` |
| Frontend | `frontend/src/components/feed/PostHeaderActions.tsx` |
| Frontend | `frontend/src/components/feed/FeedPostCard.tsx` |
| Frontend | `frontend/src/pages/FeedPage.tsx` |
| Frontend | `frontend/src/pages/FeedPostDetailPage.tsx` |
| Frontend | `frontend/src/pages/ProfilePage.tsx` |
| Frontend | `frontend/src/pages/PublicProfilePage.tsx` |
| Docs | `docs/superpowers/specs/2026-08-04-feed-post-delete-menu-design.md` |

## Verification

```bash
make backend-test-one target='src/tests/api/test_feed_posts_routes.py::test_feed_post_delete_success src/tests/api/test_feed_posts_routes.py::test_feed_post_delete_forbidden_non_owner src/tests/api/test_feed_posts_routes.py::test_feed_post_delete_not_found'
# 3 passed in 1.37s

cd frontend && npm run lint && npm run build
# exit 0
```

## Known limitations / next steps

- No admin/moderator delete (author-only by design).
- Hard delete only — no soft-delete or undo.
- No dedicated frontend component tests for `PostHeaderActions` (same gap as comment overflow menu).
- Manual QA recommended: own post ⋯ in feed + detail; confirm copy; non-owner sees no menu.
