# Feed post delete + owner overflow menu

## Metadata
- Feature slug: `feed-post-delete-menu`
- Author: Agent
- Created at: 2026-08-04
- Priority: high
- Target area: fullstack

## Problem
- Authors cannot delete their feed posts; mistakes and unwanted posts persist.
- Edit affordance is an inline «Редактировать» text link, inconsistent with comment threads that use a ⋯ overflow menu (Изменить / Удалить).

## Scope
- **Backend:** `DELETE /api/feed-posts/{post_id}` — author-only hard delete; comments removed via DB `ON DELETE CASCADE` on `feed_post_comment.feed_post_id`.
- **Frontend:** ⋯ overflow menu on own posts in feed (`FeedPostCard`) and detail (`FeedPostDetailPage`), matching comment owner actions: **Изменить** / **Удалить**.
- Remove standalone inline «Редактировать» button; edit enters via overflow menu.
- Confirm delete with `window.confirm` before calling API (copy mentions comments).
- Pytest for new API; frontend lint/build clean for touched files.

## Out of scope
- Admin/moderator delete (no admin role).
- Soft-delete or undo.
- Delete from surfaces beyond feed card and post detail (profile/public profile lists use same `FeedPostCard` — covered).

## Acceptance Criteria
- [ ] Author can delete own post → `204`; associated comments are gone from DB.
- [ ] Non-author receives `403`; missing post `404`.
- [ ] Own posts show ⋯ menu in `FeedPostCard` and on detail with **Изменить** / **Удалить**.
- [ ] Delete confirms with text mentioning comments; after delete feed removes card / detail navigates away.
- [ ] `pytest` covers new API (happy path, 403, 404); frontend lint/build clean for touched files.

## Constraints
- Mirror `DeleteFeedPostCommentService` shape: `@dataclass`, `build(session)`, `execute(...)`, typed errors mapped in route.
- Reuse or thin-wrap `CommentHeaderActions` overflow pattern for post header (no Reply/Share unless already present).
- Hard delete only; rely on existing FK CASCADE — no manual comment cleanup in service.
