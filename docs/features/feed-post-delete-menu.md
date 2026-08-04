# Feed post delete + owner overflow menu

## Summary

Authors can delete their feed posts. Edit and delete live in a ⋯ overflow menu on own posts (feed cards and detail), matching comment owner actions. Inline «Редактировать» text link removed from post headers.

## API

| Method | Path | Auth | Response |
|--------|------|------|----------|
| `DELETE` | `/api/feed-posts/{post_id}` | Author | `204 No Content` |

Errors: `404` post not found, `403` non-owner.

Comments on the post are removed via DB `ON DELETE CASCADE` on `feed_post_comment.feed_post_id` — no manual comment cleanup in the service.

## Backend

- `backend/src/services/feed_posts/delete_feed_post.py` — `DeleteFeedPostService.build(session).execute(feed_post_id, actor_user_id)`
- Reuses `FeedPostNotFoundError` and `FeedPostForbiddenError` from sibling feed-post services
- Route: `backend/src/api/feed_posts/routes.py` — `delete_feed_post_route`

## Frontend

- `frontend/src/api/feedPostApi.ts` — `deleteFeedPost(postId)`
- `frontend/src/components/feed/PostHeaderActions.tsx` — ⋯ menu: **Изменить**, **Удалить**, **Удаление…**
- `frontend/src/components/feed/FeedPostCard.tsx` — menu for own posts; confirm: «Удалить пост? Комментарии тоже будут удалены.»; `onPostDeleted` callback
- Parents: `FeedPage`, `FeedPostDetailPage`, `ProfilePage`, `PublicProfilePage` — list removal or navigate away after delete

## Tests

```bash
make backend-test-one target='src/tests/api/test_feed_posts_routes.py::test_feed_post_delete_success src/tests/api/test_feed_posts_routes.py::test_feed_post_delete_forbidden_non_owner src/tests/api/test_feed_posts_routes.py::test_feed_post_delete_not_found'
```

Status: passed (2026-08-04, 3 passed).

```bash
cd frontend && npm run lint && npm run build
```

Status: passed (2026-08-04, exit 0).

## Out of scope

- Admin/moderator delete
- Soft-delete or undo
- Delete surfaces beyond feed card and post detail (profile lists use same `FeedPostCard` — covered)
