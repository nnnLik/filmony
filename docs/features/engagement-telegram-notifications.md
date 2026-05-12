# Engagement Telegram notifications

## Поведение

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
- **Реакция на карточку или комментарий**: при **добавлении** реакции владелец цели получает DM; при **снятии** той же реакции уведомление не отправляется.
- Реакция «на себя» не шлёт уведомление (владелец = автор действия).

Ошибки Telegram (нет чата с ботом, сеть) **не влияют** на HTTP-ответ API; пишутся в лог.

## Связанные файлы

- `backend/src/services/telegram/mini_app_link.py`
- `frontend/src/navigation/TelegramMiniAppStartParamRedirect.tsx`
- `backend/src/services/telegram/engagement_delivery.py`
- `backend/src/services/telegram/notify_comment_reply.py`
- `backend/src/services/telegram/notify_feed_post_comment_reply.py`
- `backend/src/services/telegram/notify_feed_post_root_comment.py`
- `backend/src/services/telegram/notify_reaction_added.py`
- `backend/src/services/telegram/notify_movie_card_root_comment.py`
- `backend/src/services/reactions/set_or_toggle_user_reaction.py` — `SetUserReactionOutcome.reaction_was_added`
- Доставка через **Celery** (`tasks.telegram_engagement.*`), воркер `celery-worker`. История: раньше использовались `BackgroundTasks`.

## Тесты

`backend/src/tests/api/test_engagement_telegram_notifications.py`
