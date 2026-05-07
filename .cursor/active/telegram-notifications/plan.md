# Plan — telegram-notifications MVP

1. Инфраструктура: `integrations/telegram` — вызов `sendMessage`, разбор `ok: false`.
2. Сервис: классификация ошибок Telegram → `TelegramChatUnavailableError`.
3. Роут `POST /api/me/notifications/ping` → сервис → HTTPException с `detail` dict + `bot_username`.
4. Тесты: pytest + мок ответа Telegram.
5. Фронт: `postNotificationPing`, парсинг ошибки, секция на `ProfilePage`.
6. Документация: `docs/features/telegram-notifications.md`, action-log.
