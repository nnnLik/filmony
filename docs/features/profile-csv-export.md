# Экспорт карточек в CSV (Telegram)

## Назначение

Пользователь может выгрузить **все** свои карточки фильмов в CSV. Файл приходит **в личные сообщения с ботом** Filmony (Telegram Bot API `sendDocument`), а не через скачивание в мини-приложении.

## API

`POST /api/me/cards/export-csv`

- Требуется сессия (cookie).
- Успех: `{ "status": "sent" }`.
- `422` + `detail.code === "telegram_chat_unavailable"` — пользователь не открыл чат с ботом (нужен Start). В `detail.bot_username` — имя бота для deep link.
- `502` + `telegram_delivery_failed` — сбой доставки в Telegram.

## Формат CSV

UTF-8 с BOM. Заголовок:

`card_id`, `film_id`, `kinopoisk_id`, `title`, `year`, `genres` (через `|`), `rating`, `company`, `mood_before`, `mood_after`, `custom_tags` (через `;`), `poster_url`, `updated_at` (ISO 8601).

## UI

Экран **Профиль** ([ProfilePage](frontend/src/pages/ProfilePage.tsx)): кнопка с иконкой загрузки в шапке (рядом с переходом в настройки). После успеха показывается подсказка открыть чат с ботом; при отсутствии чата — блок «Нужен чат с ботом» и кнопка «Открыть бота».

## Тесты

`backend/src/tests/api/test_me_cards_export_csv.py` — мок `TelegramBotApiClient.send_document_multipart`.
