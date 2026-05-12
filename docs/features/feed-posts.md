# Посты ленты (FeedPost)

Текстовый элемент глобальной ленты: до **2000** символов plain text, опционально одна картинка, опциональная привязка к `movie_card` и/или публикация из **своего** комментария к карточке.

## Модель

Таблица `feed_post`: `user_id`, `body`, `image_url`, `referenced_movie_card_id`, `source_comment_id`, `created_at`. FK на карточку и комментарий — `ON DELETE SET NULL`.

## API

Все пути с префиксом `/api/feed-posts`. Кроме прокси медиа — **Bearer обязателен**.

| Метод | Путь | Ответ (суть) |
|--------|------|----------------|
| `POST` | `/api/feed-posts` | `FeedPostResponse` — сырой пост после создания |
| `GET` | `/api/feed-posts/{post_id}` | `FeedPostFeedItemResponse` — как элемент ленты: автор, реакции, превью комментариев, сниппеты по телу и `source_comment` |
| `POST` | `/api/feed-posts/upload` | `{ "url": string }` — картинка в RustFS |
| `GET` | `/api/feed-posts/media/{media_key}` | бинарный поток (**без** Bearer, для `<img src>`) |
| `GET` | `/api/feed-posts/{post_id}/comments` | корни, `cursor`, `limit` ≤ 50 |
| `GET` | `/api/feed-posts/{post_id}/comments/{comment_id}/replies` | ответы |
| `POST` | `/api/feed-posts/{post_id}/comments` | комментарий или ответ |

**Создание поста** (`POST /api/feed-posts`): `body` (по умолчанию `''`), `image_url`, `referenced_movie_card_id`, `source_comment_id` — опционально; контент обязателен: непустой `body` после нормализации и/или непустой `image_url` после нормализации.

Если задан `source_comment_id`, комментарий должен быть **ваш**; при несовпадении переданного `referenced_movie_card_id` с карточкой комментария — `400`. Карточка подставляется из комментария; **текст поста только из `body`**. При конвертации из комментария картинка поста берётся из `comment.image_url` (одна картинка на пост).

## Текст поста: токены

Валидация: `validate_feed_post_body` → `services/feed_posts/validate_feed_post_body.py`.

- Реакции: `⟦r{id}⟧`, `id` — существующий `ReactionType`.
- Inline-карточки: `⟦c{movie_card_id}⟧` — только **ваши** карточки (`MovieCard.user_id` = автор поста); иначе `400`.
- Упоминания: `⟦@profile_slug⟧` (канон в lower case), только **подписки** (`follower` = автор, `following` = упомянутый), не себя — см. логику в `validate_and_canonicalize_mentions`.

В ответах ленты и `GET /api/feed-posts/{post_id}` поля **`body_referenced_movie_cards`**, **`body_referenced_mentions`** — сниппеты по телу поста; в **`source_comment`** — то же для текста исходного комментария (плюс автор, `image_url`).

## Комментарии к посту

Текст **1…250** символов; токены как у комментария к карточке (`validate_comment_text_with_reaction_tokens`). В ответах: `referenced_movie_cards`, `referenced_mentions`, реакции, счётчики ветки.

## Telegram

- Упоминания в **теле нового поста** → Celery `notify_feed_post_mentions`; диплинк `?startapp=p<post_id>` (`mini_app_link.py`, клиент `TelegramMiniAppStartParamRedirect`).
- **Комментарии** к посту (корень, ответ, @ в тексте) → [`engagement-telegram-notifications.md`](./engagement-telegram-notifications.md).

## Сервисы (backend)

| Зона | Файлы |
|------|--------|
| Создание / валидация тела | `create_feed_post.py`, `validate_feed_post_body.py` |
| Образ ленты по id | `get_feed_post_feed_item.py` |
| Картинка | `upload_feed_post_image.py` (лимит байт — `FEED_POST_IMAGE_MAX_BYTES` в пакете `services.feed_posts`) |
| Комментарии | `create_feed_post_comment.py`, `list_feed_post_comments.py` |
| HTTP | `api/feed_posts/routes.py`, схемы в `api/feed_posts/schemas.py` + `FeedPostFeedItemResponse` в `api/cards/schemas.py` |
| Сниппеты inline | `batch_resolve_inline_movie_card_refs`, `batch_resolve_inline_mentions` + маппинг `api/cards/feed_post_feed_mapping.py` |

## Фронтенд

- Композер: `FeedComposeSheet` — подписки для `@`, `MovieCardInlinePickerButton` → токены `⟦c{id}⟧`.
- Рендер тела поста и комментариев: `CommentBodyWithReactionTokens` + сниппеты с API.

## Тесты

`backend/src/tests/api/test_feed_posts_routes.py` — создание, комментарии, упоминания, моки Celery. Регистрация задач: `backend/src/tests/test_celery_app.py`. Диплинк: `backend/src/tests/services/test_mini_app_link.py`.

```bash
make backend-test-one target=src/tests/api/test_feed_posts_routes.py
```

## Не делаем / ограничения

- Нет редактирования и удаления постов.
- DM не уходит без чата с ботом у получателя.
- Смена `profile_slug` ломает старые `⟦@…⟧` в сохранённом тексте.
