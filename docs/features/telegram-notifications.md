# Telegram notifications (MVP)

## Что сделано

- Исходящие личные сообщения через **Telegram Bot API** (`sendMessage`), токен тот же, что для Mini App: **`TG_APP_TOKEN`**.
- Сервис **`SendTelegramBotMessageService`** (`backend/src/services/telegram/send_bot_message.py`) и HTTP-клиент **`TelegramBotApiClient`** (`backend/src/integrations/telegram/bot_api_client.py`).
- Эндпоинт **`POST /api/me/notifications/ping`** — отправляет текущему пользователю тестовое сообщение в чат с ботом.
- Если пользователь **не начинал диалог с ботом** (не нажал Start), заблокировал бота и т.п., API отвечает **422** с телом вида:
  - `code`: `telegram_chat_unavailable`
  - `message`: текст для пользователя
  - `bot_username`: из **`TELEGRAM_BOT_USERNAME`** — чтобы фронт открыл `https://t.me/<username>`
- Прочие сбои Telegram → **502**, `code`: `telegram_delivery_failed`.
- На экране **Профиль** добавлен блок «Уведомления в Telegram» с кнопкой проверки и карточкой ошибки + «Открыть бота» при `telegram_chat_unavailable`.

## Настройка в Telegram

1. **Один бот** для Mini App и для рассылки: токен из [@BotFather](https://t.me/BotFather) должен совпадать с **`TG_APP_TOKEN`** на бэкенде (как для проверки `initData`).
2. **Mini App**: в BotFather привяжите HTTPS URL вашего фронта к боту (Menu Button / Mini App).
3. Чтобы бот мог **писать пользователю в личку**, пользователь должен **открыть чат с ботом и нажать Start** (или «Запустить»). Без этого Bot API вернёт ошибку — мы показываем её во фронте и даём кнопку открытия бота.
4. **`TELEGRAM_BOT_USERNAME`** в env (без `@`) — для ссылки «Открыть бота» в ошибке; должен совпадать с юзернеймом бота в Telegram.

## API

| Метод | Путь | Описание |
|--------|------|----------|
| POST | `/api/me/notifications/ping` | Тестовое сообщение себе; требует сессию (cookie). Ответ 200: `{"status":"sent"}`. |

## Файлы

| Область | Путь |
|---------|------|
| Bot API клиент | `backend/src/integrations/telegram/bot_api_client.py` |
| Сервис отправки | `backend/src/services/telegram/send_bot_message.py` |
| Роуты | `backend/src/api/notifications/routes.py` |
| Регистрация роутера | `backend/src/api/router.py` |
| Тесты | `backend/src/tests/api/test_notifications_ping.py` |
| API клиент | `frontend/src/api/notificationApi.ts` |
| Ошибки / ссылки | `frontend/src/lib/telegramNotificationError.ts` |
| UI | `frontend/src/pages/ProfilePage.tsx` |

## Дальше (не в этом MVP)

- Очередь (Celery), дедупликация, события домена (друзья, шаринг карточек) — см. `.cursor/features/009-telegram-notifications.md`.
