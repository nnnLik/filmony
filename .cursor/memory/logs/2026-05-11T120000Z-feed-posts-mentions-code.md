# Action log — feed-posts mentions

- **Timestamp:** 2026-05-11T12:00:00Z
- **Feature slug:** feed-posts
- **Action type:** code

## Summary

Упоминания подписок в теле поста ленты: токены `⟦@profile_slug⟧`, валидация подписки, Celery + Telegram DM, UI автодополнения и подсветка, deep link `startapp=p<id>`.

## Files

- `backend/src/services/feed_posts/validate_feed_post_body.py`
- `backend/src/services/feed_posts/create_feed_post.py`
- `backend/src/services/feed_posts/__init__.py`
- `backend/src/services/telegram/notify_feed_post_mention.py`
- `backend/src/services/telegram/mini_app_link.py`
- `backend/src/tasks/telegram_engagement.py`
- `backend/src/api/feed_posts/routes.py`
- `backend/src/tests/api/test_feed_posts_routes.py`
- `backend/src/tests/test_celery_app.py`
- `backend/src/tests/services/test_mini_app_link.py`
- `frontend/src/lib/commentReactionTokens.ts`
- `frontend/src/lib/feedMentionCompose.ts`
- `frontend/src/components/comments/CommentBodyWithReactionTokens.tsx`
- `frontend/src/components/comments/CommentDraftMirrorField.tsx`
- `frontend/src/components/feed/FeedComposeSheet.tsx`
- `frontend/src/components/feed/FeedPostCard.tsx`
- `frontend/src/navigation/TelegramMiniAppStartParamRedirect.tsx`
- `frontend/src/pages/FeedPage.tsx`
- `docs/features/feed-posts.md`

## Verification

```bash
docker compose -f docker-compose.yml exec -w /opt/app backend pytest src/tests/api/test_feed_posts_routes.py src/tests/test_celery_app.py src/tests/services/test_mini_app_link.py -q
docker compose -f docker-compose.yml exec -w /opt/app backend ruff check src/services/feed_posts src/services/telegram/notify_feed_post_mention.py src/services/telegram/mini_app_link.py src/api/feed_posts/routes.py src/tasks/telegram_engagement.py
cd frontend && npm run build
```
