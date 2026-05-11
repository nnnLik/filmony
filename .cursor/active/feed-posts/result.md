# Result: feed-posts (включая @упоминания)

## Сделано

- Посты ленты: таблица `feed_post`, создание/чтение, `POST`/`GET` `/api/feed-posts`, загрузка изображения.
- **Упоминания:** в теле поста допускаются токены `⟦@profile_slug⟧` (уникальный ник в БД — `user.profile_slug`). Разрешены только пользователи, на которых автор **подписан** (`user_subscription`). Нельзя упомянуть себя.
- После создания поста с упоминаниями ставится задача Celery `tasks.telegram_engagement.notify_feed_post_mentions` → HTML DM через `deliver_engagement_html_message` (как у других engagement-уведомлений), ссылка «Открыть пост в ленте» с `https://t.me/<bot>/app?startapp=p<post_id>`.
- **Фронт:** при вводе `@` показывается список подписок (`GET /api/users/{me}/subscriptions?type=following`), вставка токена; зеркало черновика и карточка поста рендерят упоминания янтарным бейджем; редирект по `p<id>` на главную с подсветкой `data-feed-post-id`.

## Файлы (ключевые)

- `backend/src/services/feed_posts/validate_feed_post_body.py`, `create_feed_post.py`
- `backend/src/services/telegram/notify_feed_post_mention.py`, `mini_app_link.py`
- `backend/src/tasks/telegram_engagement.py`, `backend/src/api/feed_posts/routes.py`
- `backend/src/tests/api/test_feed_posts_routes.py`, `test_celery_app.py`, `test_mini_app_link.py`
- `frontend/src/components/feed/FeedComposeSheet.tsx`, `FeedPostCard.tsx`
- `frontend/src/lib/commentReactionTokens.ts`, `feedMentionCompose.ts`
- `frontend/src/components/comments/CommentBodyWithReactionTokens.tsx`, `CommentDraftMirrorField.tsx`
- `frontend/src/navigation/TelegramMiniAppStartParamRedirect.tsx`, `frontend/src/pages/FeedPage.tsx`
- `docs/features/feed-posts.md`

## Проверка

```bash
make backend-test-one target=src/tests/api/test_feed_posts_routes.py
docker compose -f docker-compose.yml exec -w /opt/app backend pytest src/tests/test_celery_app.py src/tests/services/test_mini_app_link.py -q
cd frontend && npm run build
```

## Ограничения

- Уведомление в Telegram не дойдёт, если у получателя нет чата с ботом (как у прочих engagement-уведомлений).
- Смена `profile_slug` ломает старые токены в тексте.
