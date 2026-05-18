# Engagement Telegram notifications

## Поведение

### Публикация контента подписчикам (авто)

- **`POST /api/cards`** (новая карточка): все **подписчики** автора получают DM «опубликовал(а) новую карточку» со ссылкой `startapp=c<id>`.
- **`POST /api/feed-posts`** (новый пост ленты): подписчикам отправляется DM «опубликовал(а) пост в ленте» со ссылкой `startapp=p<id>`; пользователи, которые уже получают DM об **упоминании** в тексте этого поста, из рассылки **исключаются**.
- Подробные шаблоны текста HTML: **[`followed-content-notifications.md`](./followed-content-notifications.md)**.

### Комментарии к карточке фильма (`POST /api/cards/{id}/comments`)

- **Корневой комментарий** (`parent_comment_id` нет): владелец карточки получает DM (если комментарий не свой).
- **Ответ** (`parent_comment_id`): автор родительского комментария получает DM (если ответил не он сам).
- Ссылка в DM: «Открыть в Filmony» → `https://t.me/<bot>/app?startapp=c<card_id>`. Клиент: `initDataUnsafe.start_param` → `/cards/:id`.

### Комментарии к посту ленты (`POST /api/feed-posts/{id}/comments`)

- **Корневой комментарий**: автор поста получает DM (если комментарий не свой).
- **Ответ**: автор родительского комментария получает DM (если ответил не он сам).
- Ссылка: «Открыть пост в ленте» → `https://t.me/<bot>/app?startapp=p<post_id>`.

### Прочее

- **@упоминания** в тексте поста или комментария (карточка / пост ленты): отдельные задачи Celery; получатели, совпадающие с автором уведомления о корне/ответе (чтобы не дублировать), из списка упоминаний исключаются в роуте.
- **Новая карточка / новый пост в ленте:** подписчики автора получают отдельное авто-уведомление в Telegram; для поста адресаты @упоминаний **не** получают второе «новый пост»-уведомление (см. [`followed-content-notifications.md`](./followed-content-notifications.md)).
- **Реакция на карточку или комментарий**: при **добавлении** реакции владелец цели получает DM; при **снятии** той же реакции уведомление не отправляется.
- Реакция «на себя» не шлёт уведомление (владелец = автор действия).

Ошибки Telegram (нет чата с ботом, сеть) **не влияют** на HTTP-ответ API; пишутся в лог.

## Связанные файлы

- `backend/src/services/telegram/notify_follower_new_user_card.py`
- `backend/src/services/telegram/notify_follower_new_feed_post.py`
- `backend/src/services/subscriptions/list_follower_user_ids_for_following_user.py`
- `backend/src/services/telegram/mini_app_link.py`
- `frontend/src/navigation/TelegramMiniAppStartParamRedirect.tsx`
- `backend/src/services/telegram/engagement_delivery.py`
- `backend/src/services/telegram/notify_comment_reply.py`
- `backend/src/services/telegram/notify_feed_post_comment_reply.py`
- `backend/src/services/telegram/notify_feed_post_root_comment.py`
- `backend/src/services/telegram/notify_reaction_added.py`
- `backend/src/services/telegram/notify_movie_card_root_comment.py`
- `backend/src/services/reactions/set_or_toggle_user_reaction.py` — `SetUserReactionOutcome.reaction_was_added`
- `backend/src/services/telegram/notify_follower_new_user_card.py`
- `backend/src/services/telegram/notify_follower_new_feed_post.py`
- Доставка через **Celery** (`tasks.telegram_engagement.*`), воркер `celery-worker`. История: раньше использовались `BackgroundTasks`.

## Тесты

`backend/src/tests/api/test_engagement_telegram_notifications.py`
