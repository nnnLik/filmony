# Feature Request

## Metadata
- Feature slug: `comment-edit-delete`
- Author: Agent
- Created at: 2026-07-23
- Priority: high
- Target area: fullstack

## Problem
- Authors cannot edit or delete their comments on feed posts or user cards.
- Mistakes and unwanted comments persist with no self-service fix.

## Scope
- In scope:
  - Author-only `PATCH` and `DELETE` for feed post comments and user card comments.
  - Frontend edit/delete affordances on post detail and card detail comment threads.
  - Pytest coverage for new endpoints and authorization.
- Out of scope:
  - Admin/moderator delete (no admin role in repo).
  - Soft-delete; follow existing hard-delete + DB CASCADE for reply trees.
  - Editing comments on feed preview cards (detail pages only).

## Functional Requirements
- [ ] `PATCH /api/feed-posts/{post_id}/comments/{comment_id}` — author updates text.
- [ ] `DELETE /api/feed-posts/{post_id}/comments/{comment_id}` — author hard-deletes (replies CASCADE).
- [ ] `PATCH /api/cards/{card_id}/comments/{comment_id}` — author updates text and optional image.
- [ ] `DELETE /api/cards/{card_id}/comments/{comment_id}` — author hard-deletes.
- [ ] Non-authors receive `403`; wrong parent resource `404`.
- [ ] UI: author sees «Редактировать» / «Удалить» on own comments.

## Acceptance Criteria
- [ ] Author can edit comment text (and card comment image) and see updated thread.
- [ ] Author can delete own comment; thread and counts update without breaking list/create flows.
- [ ] Other users cannot edit/delete (`403`).
- [ ] Tests pass in Docker (`make backend-test-one` for new cases).

## Constraints
- One service per use case with `build()` / `execute()`.
- Reuse comment text validation (reaction tokens, mentions) from create flows.
- Hard delete matching `DeleteUserCardService` pattern.
