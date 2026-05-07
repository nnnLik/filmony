# Engagement Telegram notifications

## Поведение

- **Ответ на комментарий** (`parent_comment_id`): автор родительского комментария получает DM (если ответил не он сам).
- **Реакция на карточку или комментарий**: при **добавлении** реакции владелец цели получает DM; при **снятии** той же реакции уведомление не отправляется.
- Реакция «на себя» не шлёт уведомление (владелец = автор действия).

Формат: короткий текст с эмодзи (⭐ ответ/реакция, 👤 автор, 📝 цитата ответа, 🎬 ссылка на карточку). **Без** слова «уведомление», **без** ❤️ и **без** названия типа реакции из каталога — только факт «отреагировал». Deep link на контекст карточки: **`https://t.me/<bot>?startapp=c<card_id>`** (кликабельный текст «Карточка №…»), одинаково для реакции на карточку и на комментарий (комментарий привязан к этой карточке).

Ошибки Telegram (нет чата с ботом, сеть) **не влияют** на HTTP-ответ API; пишутся в лог.

## Связанные файлы

- `backend/src/services/telegram/engagement_delivery.py`
- `backend/src/services/telegram/notify_comment_reply.py`
- `backend/src/services/telegram/notify_reaction_added.py`
- `backend/src/services/telegram/mini_app_link.py`
- `backend/src/services/reactions/set_or_toggle_user_reaction.py` — `SetUserReactionOutcome.reaction_was_added`
- Доставка через **Celery** (`tasks.telegram_engagement.*`), воркер `filmony-celery-worker`. История: раньше использовались `BackgroundTasks`.

## Тесты

`backend/src/tests/api/test_engagement_telegram_notifications.py`
