# Plan: comment-edit-delete

## 1. Backend — feed post comments
1. `UpdateFeedPostCommentService` — load comment, verify `feed_post_id` + author, normalize text, commit.
2. `DeleteFeedPostCommentService` — load comment, verify post + author, hard delete.
3. Schemas: `FeedPostCommentUpdateRequest`.
4. Routes: `PATCH` + `DELETE` on `/{post_id}/comments/{comment_id}`.

## 2. Backend — user card comments
1. `UpdateUserCardCommentService` — same + optional `image_url` (create validation).
2. `DeleteUserCardCommentService` — verify card + author, hard delete.
3. Schemas: `UserCardCommentUpdateRequest`.
4. Routes: `PATCH` + `DELETE` on `/{card_id}/comments/{comment_id}`.

## 3. Tests
- Happy path edit/delete for both targets.
- `403` for non-author, `404` for wrong post/card id.

## 4. Frontend
- API helpers in `feedPostApi.ts` and `cardApi.ts`.
- `CommentOwnerActions` component (edit/delete + inline edit form).
- Wire into `FeedPostDetailPage` and `MovieCardDetailPage`.

## 5. Docs & workflow
- `progress.md`, `result.md`, `docs/features/comment-edit-delete.md`, action log.
