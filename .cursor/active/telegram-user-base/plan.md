# Implementation Plan

## Feature
- Slug: `telegram-user-base`
- Source spec: `.cursor/features/telegram-user-base/feature.md` (и `.cursor/features/001-telegram-user-base.md`)

## Goal
- Бэкенд: валидация initData (HMAC WebAppData), таблица пользователя в PostgreSQL, JWT-сессия в httpOnly cookie, эндпоинты `/api/auth/telegram`, `/api/me`, `/api/auth/logout`.
- Фронт: обмен initData на сессию, отображение пользователя с бэкенда (по мере готовности).
- Инфра: Alembic, compose Postgres, тесты на той же БД в отдельной схеме.

## Step-by-Step Plan (фактический порядок работ)
1. Настройки: `DatabaseSettings`, `TelegramAuthSettings`, `AuthJwtSettings`, `AppEnv.TEST` для pytest.
2. `core/database.py`: asyncpg, `search_path` для `ENV=test` + `DATABASE_TEST_SCHEMA`.
3. Модель `User`, миграция Alembic (`src/migrations`), `compose.yml` + Postgres.
4. Сервисы: `VerifyTelegramInitDataService`, `UpsertTelegramUserService`, `IssueSessionJwtService`, `DecodeSessionJwtService`.
5. Роуты `api/auth`, зависимость `CurrentUser`, `GET /api/me` на `api/router`.
6. Тесты: `test_telegram_auth.py`, хелпер подписи initData, `conftest.py` (схема, таблицы).
7. Репозиторий: `.gitignore`, `README.md`, `vars/.env.example`; правка предупреждения Pydantic (`default_schema` вместо `schema`).

## Files Expected To Change / Changed
- `backend/src/conf/settings.py`
- `backend/src/core/database.py`
- `backend/src/api/auth/*`, `backend/src/api/router.py`
- `backend/src/deps/*`, `backend/src/services/auth/*`
- `backend/src/models/user.py`, `backend/src/migrations/*`
- `backend/src/tests/*`, `compose.yml`, `Makefile`, `Dockerfile`
- Корень: `.gitignore`, `README.md`, `vars/.env.example`

## Verification Plan
- `make backend-test` (внутри Docker, compose up).
- `make migrate` после изменений схемы.
- Ручная проверка: POST `/api/auth/telegram` с валидным initData в TMA (при наличии токена).

## Risks And Mitigations
- Секреты в отслеживаемых env-файлах — `.gitignore` + `vars/.env.example`; ротация уже утёкших токенов вручную.
