# Feed post edit + unlimited body

## Summary

- Removed the **2000-character product limit** on feed post bodies.
- Server-side **DoS safety cap: 100_000** characters (`FEED_POST_BODY_MAX_LEN` in `validate_feed_post_body.py`).
- DB column `feed_post.body` is **`Text`** (migration `l7m8n9o0p123`).
- Authors can **`PATCH /api/feed-posts/{post_id}`** with `{ "body": string }` (image unchanged).

## API

| Method | Path | Auth | Body |
|--------|------|------|------|
| `PATCH` | `/api/feed-posts/{post_id}` | Author | `{ "body": string }` |

Responses: `FeedPostFeedItemResponse` (same shape as `GET`).

Errors: `404` not found, `403` non-owner, `400` validation (empty body when post has no image, token/mention errors).

## Frontend

- `FeedComposeSheet`: no `maxLength` or character counter.
- Own posts: **Редактировать** on `FeedPostCard` (feed + detail); inline save/cancel.

## Limits removed

| Layer | Before | After |
|-------|--------|-------|
| DB | `VARCHAR(2000)` | `TEXT` |
| Pydantic create | `max_length=2000` | none |
| Service validation | 2000 | 100_000 (safety) |
| Compose UI | `maxLength={2000}`, char counter | unlimited |

## Tests

```bash
make backend-test-one target='src/tests/api/test_feed_posts_routes.py::test_feed_post_create_long_body src/tests/api/test_feed_posts_routes.py::test_feed_post_update_success src/tests/api/test_feed_posts_routes.py::test_feed_post_update_forbidden_non_owner src/tests/api/test_feed_posts_routes.py::test_feed_post_update_validation_empty_without_image src/tests/api/test_feed_posts_routes.py::test_feed_post_update_not_found'
```

## Out of scope

- Delete post; edit image or card reference; re-notify mentions on edit.
