# Посты ленты (FeedPost)

## Цель

Сущность **текстового поста** в ленте: plain text (до 2000 символов), опционально одна картинка (URL / upload), опциональная ссылка на `movie_card`, опционально публикация на основе **своего** комментария к карточке.

## Модель и миграция

- Таблица `feed_post`: `user_id`, `body`, `image_url`, `referenced_movie_card_id`, `source_comment_id`, `created_at`.
- FK: карточка и комментарий — `ON DELETE SET NULL`.

## API

| Метод | Путь | Auth |
|--------|------|------|
| `POST` | `/api/feed-posts` | да |
| `GET` | `/api/feed-posts/{post_id}` | да |
| `POST` | `/api/feed-posts/upload` | да |

Тело создания: `body` (по умолчанию `''`), `image_url`, `referenced_movie_card_id`, `source_comment_id` — опциональны при непустом контенте: нужен непустой `body` после нормализации и/или `image_url`.

Если передан `source_comment_id`, комментарий должен принадлежать текущему пользователю; `referenced_movie_card_id` выводится из комментария; пустой `body` заполняется текстом комментария.

## Тело поста: реакции и @упоминания

- Встроенные токены реакций: `⟦r{id}⟧` (как в комментариях).
- **Упоминания подписок:** канонический токен `⟦@profile_slug⟧`, где `profile_slug` — уникальный slug пользователя в БД (`user.profile_slug`, сравнение без учёта регистра; в сохранённом тексте slug канонизируется в lower case).
- Разрешено упоминать только пользователей, на которых автор поста **подписан** (`user_subscription`: `follower_user_id` = автор, `following_user_id` = упомянутый). Нельзя упомянуть себя. Иначе `400` с текстом ошибки валидации.

## Telegram

После успешного `POST /api/feed-posts` при наличии валидных упоминаний в очередь ставится Celery-задача `tasks.telegram_engagement.notify_feed_post_mentions` (см. `backend/src/tasks/telegram_engagement.py`). Для каждого получателя отправляется HTML-сообщение (`services/telegram/notify_feed_post_mention.py`, `deliver_engagement_html_message`).

Deep link на мини-приложение: `telegram_mini_app_feed_post_url` / `html_feed_post_deep_link_block` в `services/telegram/mini_app_link.py` — формат `?startapp=p<post_id>`. Клиент обрабатывает `p<id>` в `TelegramMiniAppStartParamRedirect` и открывает ленту с подсветкой поста (`data-feed-post-id`).

## Сервисы (backend)

- `CreateFeedPostService` → `CreateFeedPostResult` (`post`, `mentioned_user_ids`) — `services/feed_posts/create_feed_post.py`
- `GetFeedPostByIdService` — `services/feed_posts/get_feed_post_by_id.py`
- `validate_feed_post_body(text, session, author_user_id=...)` — реакции + упоминания — `services/feed_posts/validate_feed_post_body.py`

## Фронтенд

- Композер: `FeedComposeSheet` — загрузка подписок `getUserSubscriptions(me, 'following')`, попап при `@`, вставка `mentionTokenFromProfileSlug`.
- **Комментарии к карточке:** то же поведение `@` на странице деталки (`MovieCardDetailPage`) — список подписок и токены `⟦@slug⟧`.
- Отображение тела: `CommentBodyWithReactionTokens` + `splitCommentTextIntoSegments` — сегменты `mention` с янтарным бейджем; карточка `FeedPostCard` и текст комментариев.

## Тесты

- `backend/src/tests/api/test_feed_posts_routes.py` — в т.ч. упоминания и мок Celery.
- `backend/src/tests/test_celery_app.py` — регистрация `notify_feed_post_mentions`.
- `backend/src/tests/services/test_mini_app_link.py` — URL `p<id>`.

Прогон: `make backend-test-one target=src/tests/api/test_feed_posts_routes.py`

## Не входит / ограничения

- Редактирование и удаление постов.
- Уведомление не доставляется без активного чата с ботом у получателя.
- После смены `profile_slug` старые токены в тексте перестают валидироваться.
