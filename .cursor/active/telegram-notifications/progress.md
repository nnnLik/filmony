# Progress — telegram-notifications

- Спецификация: `.cursor/features/telegram-notifications/feature.md`, план: `plan.md`.
- Реализованы клиент Bot API, сервис, `POST /api/me/notifications/ping`, тесты (файл `test_notifications_ping.py`).
- Фронт: секция на `ProfilePage`, парсинг `telegram_chat_unavailable`, `notificationFailureMessage` для прочих ошибок.
- Документация: `docs/features/telegram-notifications.md`, запись в action-log.
