# Feature: Telegram user base (`telegram-user-base`)

Публичная выжимка для продукта и онбординга разработчиков. Детальный бэклог: [`.cursor/features/001-telegram-user-base.md`](../../.cursor/features/001-telegram-user-base.md).

## Назначение

Слой доверенной идентичности для Telegram Mini App: проверка `initData`, сохранение пользователя в PostgreSQL, сессия на JWT в httpOnly cookie, защищённый профиль `GET /api/me`.

## Когда пользователь появляется в базе (важно)

**Нажатие «Старт» в чате с ботом само по себе запросов на ваш FastAPI не шлёт.** В этом репозитории пока **нет** webhook/long polling, который обрабатывал бы `/start` и создавал бы строку в `user`.

Пользователь **создаётся и обновляется** только когда клиент Mini App вызывает:

`POST /api/auth/telegram` с полем `initData` (подписанная строка из Telegram Web App).

То есть цепочка такая: пользователь **открывает Mini App** (кнопка меню, inline-кнопка с типом Web App, ссылка из настроек бота и т.д.) → фронт отправляет `initData` на бэкенд → бэкенд проверяет HMAC тем же `TG_APP_TOKEN`, что у бота → `UpsertTelegramUserService` пишет в PostgreSQL.

### Что сделать, если «в боте жму Старт — в БД пусто»

1. Убедиться, что пользователь **открывает именно Mini App** (Web App), а не только переписку с ботом.
2. В [@BotFather](https://t.me/BotFather) задать **Menu Button** / кнопку с URL вашего Mini App (**HTTPS** в проде; для локальной отладки обычно нужен туннель ngrok/cloudflared и тот же URL в настройках бота и в Telegram).
3. Проверить в DevTools / логах, что с фронта уходит `POST …/api/auth/telegram` при открытии приложения через nginx (**`http://127.0.0.1:8888`** в локальном compose) и что `VITE_API_ORIGIN` в `vars/` согласован с этим URL (см. `frontend/vite.config.ts`).
4. `TG_APP_TOKEN` в env бэкенда должен совпадать с **токеном того же бота**, чей Mini App открываете (иначе проверка подписи `initData` даст 401 и пользователь не создастся).

Если нужно, чтобы **уже на `/start`** бот отвечал и вёл в приложение, это отдельная задача: webhook на Bot API + ответ с кнопкой «Открыть Filmony» (`web_app`). Создание записи в БД по-прежнему безопасно делать только через `initData` при открытии Mini App.

## API (реализовано на бэкенде)

| Метод | Путь | Описание |
|--------|------|----------|
| POST | `/api/auth/telegram` | Тело: `initData` (или `init_data`) → проверка → upsert → Set-Cookie |
| GET | `/api/me` | Текущий пользователь; требуется cookie сессии |
| POST | `/api/auth/logout` | Очистка cookie |

## Конфигурация (env)

- `DATABASE_URL` — `postgresql://...` или уже с драйвером `postgresql+asyncpg://...` (в коде для async подставляется asyncpg).
- `DATABASE_SCHEMA` — схема приложения (в коде: `default_schema`, по умолчанию `public`)
- `DATABASE_TEST_URL` — отдельная база для pytest при `ENV=test` (создайте `CREATE DATABASE …` в кластере)
- `ENV` — `dev` | `prod` | `test` (pytest выставляет `test` в `src/tests/conftest.py` до импорта настроек)
- `TG_APP_TOKEN` / `TELEGRAM_BOT_TOKEN`, `AUTH_JWT_SECRET`, опционально `TELEGRAM_BOT_USERNAME`

Шаблон без секретов: `vars/.env.example`.

## Миграции

Из корня репозитория при поднятом compose:

```bash
make migrate
```

Alembic: `backend/alembic.ini`, скрипты в `backend/src/migrations/`.

## Тесты

```bash
make backend-test
```

Используется отдельная база из `DATABASE_TEST_URL` (тот же кластер Postgres, что и `DATABASE_URL`).

## Статус

Бэкенд и тесты готовы. На фронтенде используются `POST /api/auth/telegram`, cookie-сессия и хук **`useAuthStatus`** (`frontend/src/auth/useAuthStatus.ts`) на экранах приложения; при открытии не в Telegram часть сценариев может быть в режиме «skipped» — это ожидаемо для разработки вне TMA.
