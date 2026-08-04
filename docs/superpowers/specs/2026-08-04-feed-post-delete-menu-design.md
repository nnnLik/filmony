# Feed Post Delete + Owner Overflow Menu — Design Spec

**Date:** 2026-08-04  
**Status:** approved — Approach A  
**Feature slug:** `feed-post-delete-menu`

---

## 1. Context

Feed posts support author edit (`PATCH /api/feed-posts/{post_id}`) via an inline «Редактировать» link on `FeedPostCard`. Comments already use a ⋯ overflow menu (`CommentHeaderActions`) with **Изменить** / **Удалить** and `DELETE` API with hard delete + DB CASCADE.

Authors need to delete their own posts; UI should match comment owner-action patterns.

---

## 2. Goals

- Author can permanently delete own feed post and all its comments.
- Non-authors cannot delete (`403`); missing posts return `404`.
- Replace inline edit link with ⋯ menu on feed card and post detail (owner only).
- Confirm before delete; mention that comments will be removed.

---

## 3. Approach A (approved)

### 3.1 Backend — hard delete + CASCADE

- New `DeleteFeedPostService` mirroring `DeleteFeedPostCommentService`.
- Route: `DELETE /api/feed-posts/{post_id}` → `204`.
- No soft-delete; no explicit comment deletion in service — `feed_post_comment.feed_post_id` already has `ondelete='CASCADE'`.

### 3.2 Frontend — comment parity

- Thin `PostHeaderActions` (or reuse overflow subset of `CommentHeaderActions`): ⋯ → **Изменить** / **Удалить**.
- Remove standalone «Редактировать» text button from post header.
- Confirm: `window.confirm('Удалить пост? Все комментарии к нему тоже будут удалены.')`
- **Feed:** parent removes card from list via callback after success.
- **Detail:** navigate away (back or `/feed`) after success.
- `deleteFeedPost(postId)` in `feedPostApi.ts`.

### 3.3 Surfaces

- `FeedPostCard` (feed, profile, public profile)
- `FeedPostDetailPage` (embedded card, `linkToDetail={false}`)

---

## 4. Approaches considered

| Approach | Pros | Cons |
|----------|------|------|
| **A. Hard delete + CASCADE + ⋯ menu (approved)** | Matches comments; minimal backend; existing FK handles comments | Irreversible |
| B. Soft-delete post | Undo possible | New columns, list filters, inconsistent with comments |
| C. Keep inline edit + add delete link | Smaller UI change | Cluttered header; inconsistent with comments |

---

## 5. API contract

```http
DELETE /api/feed-posts/{post_id}
Authorization: Bearer …

204 No Content        — author deleted own post
403 Forbidden         — not the author
404 Not Found         — post does not exist
401 Unauthorized      — not logged in
```

---

## 6. Testing

- Pytest: author delete (post + comments gone), 403, 404
- Frontend: lint + build on touched files
- Manual: feed card removal, detail navigation, menu hidden for non-owner

---

## 7. Out of scope

- Moderator/admin delete
- Delete from admin tooling
- Custom modal (use `window.confirm` like comments/cards)
