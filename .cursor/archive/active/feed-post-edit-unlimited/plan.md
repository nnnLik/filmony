# Plan: feed-post-edit-unlimited

1. Migration + model: `feed_post.body` String(2000) → Text.
2. Raise `FEED_POST_BODY_MAX_LEN` to 100_000 in `validate_feed_post_body.py`; drop Pydantic 2000 cap.
3. Add `UpdateFeedPostService` + `PATCH /api/feed-posts/{post_id}`.
4. Tests in `test_feed_posts_routes.py`.
5. Frontend: remove compose limits; `updateFeedPost` API; edit UI in `FeedPostCard` + detail callback.
6. Docs + action log.
