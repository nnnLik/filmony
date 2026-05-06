# Feature: Telegram user base (`telegram-user-base`)

Публичная выжимка для продукта и онбординга разработчиков. Детальный бэклог: [`.cursor/features/001-telegram-user-base.md`](../../.cursor/features/001-telegram-user-base.md).

## Назначение

Слой доверенной идентичности для Telegram Mini App: проверка `initData`, сохранение пользователя в PostgreSQL, сессия на JWT в httpOnly cookie, защищённый профиль `GET /api/me`.

## API (реализовано на бэкенде)

| Метод | Путь | Описание |
|--------|------|----------|
| POST | `/api/auth/telegram` | Тело: `initData` (или `init_data`) → проверка → upsert → Set-Cookie |
| GET | `/api/me` | Текущий пользователь; требуется cookie сессии |
| POST | `/api/auth/logout` | Очистка cookie |

## Конфигурация (env)

- `DATABASE_URL` — `postgresql://...` или уже с драйвером `postgresql+asyncpg://...` (в коде для async подставляется asyncpg).
- `DATABASE_SCHEMA` — схема приложения (в коде: `default_schema`, по умолчанию `public`)
- `DATABASE_TEST_SCHEMA` — схема для pytest при `ENV=test`
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

Используется тот же Postgres, что и приложение; данные тестов — в схеме из `DATABASE_TEST_SCHEMA`.

## Статус

Бэкенд и тесты — базовая реализация готова. Фронт по полному списку из 001 (отдельный API-клиент, хук auth, контекст) — уточняйте в `progress.md` / следующих PR.
