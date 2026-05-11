# Plan: feed-posts (backend MVP)

1. Модель + Alembic `feed_post`.
2. Валидация тела (длина, токены реакций).
3. `CreateFeedPostService`, `GetFeedPostByIdService`, роуты, регистрация в `api/router.py`.
4. Pytest `test_feed_posts_routes.py`.
5. `docs/features/feed-posts.md`.
