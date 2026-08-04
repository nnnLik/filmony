# Feed post edit + unlimited body length

## Problem

- Feed post body is capped at 2000 characters (DB, API validation, compose UI).
- Authors cannot edit their own posts after publishing.

## Scope

- Remove the 2000-character product limit; keep a high server-side safety cap (100_000) for DoS.
- DB: `feed_post.body` → `Text`.
- Backend: `PATCH /api/feed-posts/{post_id}` — author-only body update (image unchanged).
- Frontend: remove compose `maxLength`/char counter; edit UI on own posts (feed card + detail).
- pytest: happy path, forbidden non-owner, validation.

## Out of scope

- Delete post.
- Edit image or referenced card on existing posts.
- Re-notify mentions on edit.

## Acceptance

- [ ] Posts >2000 chars can be created and retrieved.
- [ ] Author can PATCH own post body; non-owner gets 403.
- [ ] Empty body rejected when post has no image.
- [ ] Frontend lint + build pass; targeted backend tests pass in Docker.
