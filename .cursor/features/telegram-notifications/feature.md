# telegram-notifications — MVP batch 1

## Scope

- Исходящие сообщения через **Telegram Bot API** (`sendMessage`), тот же токен что и для Mini App (`TG_APP_TOKEN`).
- Эндпоинт **`POST /api/me/notifications/ping`**: тестовое сообщение текущему пользователю в личку бота.
- При недоступности чата (не нажат Start, заблокирован бот и т.п.) — ответ **422** с `detail.code === 'telegram_chat_unavailable'` и понятным текстом.
- Фронт: блок на профиле с кнопкой проверки и **понятная ошибка** + кнопка «Открыть бота».

## Acceptance criteria

- [x] Успешная отправка возвращает `{ "status": "sent" }`.
- [x] Ошибка «нет диалога с ботом» маппится в стабильный код API и красиво показывается в Mini App.
- [x] Pytest покрывает успех и ошибку чата (мок HTTP к Telegram).

## Out of scope (later)

- Celery, Redis dedupe, webhook входящих сообщений (см. `.cursor/features/009-telegram-notifications.md`).
