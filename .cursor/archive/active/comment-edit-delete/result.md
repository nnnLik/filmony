# Result: comment-edit-delete

**Status:** implemented

## Implemented

### Backend
- `UpdateFeedPostCommentService`, `DeleteFeedPostCommentService`
- `UpdateUserCardCommentService`, `DeleteUserCardCommentService`
- Routes: `PATCH`/`DELETE` on feed post and card comment paths
- Request schemas: `FeedPostCommentUpdateRequest`, `UserCardCommentUpdateRequest`
- Authorization: comment author only (no admin role in repo)
- Delete: hard delete with DB CASCADE for reply trees

### Frontend
- API: `updateFeedPostComment`, `deleteFeedPostComment`, `updateMovieCardComment`, `deleteMovieCardComment`
- `CommentOwnerActionLinks` component
- Inline edit + delete on `FeedPostDetailPage` and `MovieCardDetailPage`

### Tests
- `test_feed_post_comment_update_and_delete`
- `test_feed_post_comment_update_wrong_post`
- `test_user_card_comment_update_and_delete`
- `test_user_card_comment_update_wrong_card`

## Verification

```bash
make backend-test-one target='src/tests/api/test_feed_posts_routes.py::test_feed_post_comment_update_and_delete src/tests/api/test_feed_posts_routes.py::test_feed_post_comment_update_wrong_post src/tests/api/test_cards_routes.py::test_user_card_comment_update_and_delete src/tests/api/test_cards_routes.py::test_user_card_comment_update_wrong_card'
# 4 passed

cd frontend && npm run lint && npm run build
# OK
```

## Changed files

- `backend/src/services/feed_posts/update_feed_post_comment.py`
- `backend/src/services/feed_posts/delete_feed_post_comment.py`
- `backend/src/services/cards/update_user_card_comment.py`
- `backend/src/services/cards/delete_user_card_comment.py`
- `backend/src/api/feed_posts/schemas.py`
- `backend/src/api/feed_posts/routes.py`
- `backend/src/api/cards/schemas.py`
- `backend/src/api/cards/routes.py`
- `backend/src/tests/api/test_feed_posts_routes.py`
- `backend/src/tests/api/test_cards_routes.py`
- `frontend/src/api/feedPostApi.ts`
- `frontend/src/api/cardApi.ts`
- `frontend/src/components/comments/CommentOwnerActionLinks.tsx`
- `frontend/src/pages/FeedPostDetailPage.tsx`
- `frontend/src/pages/MovieCardDetailPage.tsx`

## Known limitations / next steps

- Card comment edit does not yet change attached image in UI (text-only inline editor; existing image preserved on save).
- Orphaned `user_reaction` rows may remain after delete (same as card delete pattern).
- No edit/delete on feed preview comment snippets (detail pages only).
