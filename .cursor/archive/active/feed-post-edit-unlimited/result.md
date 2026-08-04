# Result: feed-post-edit-unlimited

Status: **complete**

## Implemented

1. **Unlimited post body (product)** — removed 2000-char cap from DB, Pydantic create schema, compose UI; kept **100_000** server safety cap.
2. **Edit own posts** — `UpdateFeedPostService`, `PATCH /api/feed-posts/{post_id}`, inline edit on `FeedPostCard`.

## Changed files

**Backend:** `l7m8n9o0p123_feed_post_body_text.py`, `models/feed_post.py`, `validate_feed_post_body.py`, `update_feed_post.py`, `api/feed_posts/routes.py`, `api/feed_posts/schemas.py`, `tests/api/test_feed_posts_routes.py`

**Frontend:** `FeedComposeSheet.tsx`, `FeedPostCard.tsx`, `FeedPostDetailPage.tsx`, `feedPostApi.ts`, `feedMentionCompose.ts`

**Docs:** `docs/features/feed-post-edit-unlimited.md`, `docs/features/feed-posts.md`

## Verification

- Migration: `alembic upgrade head` → `l7m8n9o0p123`
- Backend: 5 new pytest cases — **all passed** (`make backend-test-one`)
- Frontend: touched files eslint clean; full `npm run build` fails on pre-existing `feedVisibleAuthorIds.test.ts` TS errors (unrelated)

## Known limitations

- No post delete; no image/card edit on PATCH; no mention re-notify on edit.
